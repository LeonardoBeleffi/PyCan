from canController import CanController, _State
from canMessage import CanMessage
import canSettings
import math

class Ecu:
    """A class used to model the High-Level ECU software.

    This acts as the base class for users. It completely hides the bit-level
    physics, exposing only logical software hooks like `setup` and `send`.

    Attributes:
        id (int): Logical identifier for the ECU.
        name (str): Human-readable name.
        message (dict): the dictionary keys are the messages id, meanwhile the values are the message info (e.g. msg frequence) 
        auto_retransmit (bool): Hardware register to toggle automatic retries.
    """

    def __init__(self, ecu_id: int, name: str, messages: dict):
        self._id = ecu_id
        self._name = name
        self._time = 0
        self._messages = messages
        self._error_state = _State.ERROR_ACTIVE

        for msg_id in self._messages.keys():
            self._messages[msg_id]["timer"] = 0
            # use microseconds instead of milliseconds
            self._messages[msg_id]["frequence"] = self._messages[msg_id]["frequence"] * 1000

        # The ECU inherently owns its CanController (hardware)
        self._controller = CanController(self._name)


    # --- Internal Bit-Level API (Called strictly by Canbus) ---
    def get_tx_bit(self) -> int:
        return self._controller.get_next_bit()

    def rx_bit(self, bit: int) -> None:
        rBit = self._controller.process_received_bit(bit)
        # bit read is the sent one and message is finished
        if rBit:
            msg_id = self._controller.get_last_message_id()
            print(f"[{self._time}] {self._name} (ID:{self._id}) sent message {msg_id}")
            self._messages[msg_id]["timer"] = self._time

        rcv_msg = self._controller.get_full_message()
        if  rcv_msg != None:
            print(f"[{self._time}] RECMSG | {self._name} received message {rcv_msg.id}")

    
    '''
        increase the ECU time. Required to simulate the ECU clock.

        Parameters:
            time_delta(int): determines how much the time increments
    '''
    def increase_time(self, time_delta: float = 10):
        if time_delta < 0:
            time_delta = 0
        self._time += time_delta
        self._controller._time += time_delta

    # returns the id of the next message to send
    def get_next_message_id(self):
        min = math.inf
        for msg_id in self._messages:
            if self._time - self._messages[msg_id]["timer"]  >= self._messages[msg_id]["frequence"] and msg_id < min:
                min = msg_id
        return min

    # create message data
    def _create_message(self, msg_id) -> CanMessage:
        # create 4 bytes message for reproducibility
        data = [0b10101010 for i in range(4)]

        msg_data = bytearray(data)
        msg = CanMessage(msg_id,msg_data)
        return msg
    
    def check_message_transmission(self,bus_idle:bool):
        
        # update error state
        if self._error_state != self._controller.get_error_state():
            self._error_state = self._controller.get_error_state()
            print(f"[{self._time}] {self._name} is in {self._error_state}")


        # cannot send messages to controller because the bus is not idle
        if not bus_idle or self._controller.get_error_state() == _State.BUS_OFF:
            return
        
        if self._controller._tec > 0 and canSettings.DEBUG:
            print(f"[{self._time}] {self._name}'s TEC: {self._controller._tec}")
        if self._controller._rec > 0 and canSettings.DEBUG:
            print(f"[{self._time}] {self._name}'s REC: {self._controller._rec}")

        # bus is idle
        msg_id = self.get_next_message_id()
        if bus_idle and msg_id != math.inf:
            message = self._create_message(msg_id)
            self._controller.queue_tx(message)
            print(f"[{self._time}] {self._name} (ID:{self._id}) is trying to send message {msg_id}")
        

class AttackerEcu(Ecu):

    def __init__(self, ecu_id, name, messages, target_id:int = -1):
        super().__init__(ecu_id, name, messages)

        # define which message to targetize
        if target_id < 0:
            target_id = iter(messages)
        self.target_id = target_id
        self.last_target_time = 0
        self.FIXED_DATA_PACKET_LENGTH = 51

        self._victim_messages_error_passive = 0 

        if not self.target_id in messages.keys():
            raise ValueError("target_id must be one of the sent messages")


    def _create_message(self, msg_id):
        msg = super()._create_message(msg_id)
        msg.data[0] = msg.data[0] - 32
        return msg
    
    def rx_bit(self, bit):
        rBit = self._controller.process_received_bit(bit)
        # bit read is the sent one and message is finished
        if rBit:
            msg_id = self._controller.get_last_message_id()
            print(f"[{self._time}] {self._name} (ID:{self._id}) sent message {msg_id}")
            self._messages[msg_id]["timer"] = self._time

        rcv_msg = self._controller.get_full_message()
        if  rcv_msg != None:
            print(f"[{self._time}] RECMSG | {self._name} received message {rcv_msg.id}")

            # update target message frequence
            if rcv_msg.id == self.target_id:  

                self.last_target_time = self._time
                self._messages[rcv_msg.id]["timer"] = self._time
                print(f"[{self._time}] ATTACKER FREQUENCE: {self._messages[rcv_msg.id]["frequence"]}")
                print(f"Next scheduled time: {self._messages[rcv_msg.id]["timer"]+self._messages[rcv_msg.id]["frequence"]}")



# workflow modification:
# if canbus is idle -> put message in controller buffer
#                        else -> I don't put anything
# on _get_tx_bit the canbus receive -> my message bit if I'm sending something
#                                   -> 1 if I'm not sending any message (in and with the other bits, it is not influent) 
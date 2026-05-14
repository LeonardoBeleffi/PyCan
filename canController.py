from canMessage import CanMessage
from collections import deque
from enum import Enum
from canFrame import *
import canSettings

class _State(Enum):
    ERROR_ACTIVE = 0
    ERROR_PASSIVE = 1
    BUS_OFF = 2


class CanController:
    """A class used to model the low-level CAN hardware.

    This class enforces the physical rules of the CAN protocol, maintains the
    Error Counters (TEC, REC), and handles bit-level state machines. It
    exposes valid hardware registers to the software (Ecu).

    Attributes:
        name (str): ecu name (for debugging purposes)

    TODO:
        - implement ack signaling
    """

    def __init__(self, name: str):
        self._last_message_id = False
        self._receiving_frame = False
        self._last_message = None
        self._error_buffer = deque()
        self._name = name
        self._bit_since_last_msg = 0

        self.reset_state()
        self.clear_tx_buffer()
        self.clear_rx_buffer()

    def clear_rx_buffer(self) -> None:
        """Flushes the hardware receive mailbox."""
        self._rx_buffer = deque()

    def clear_tx_buffer(self) -> None:
        """Flushes the hardware transmit mailbox."""
        self._tx_buffer = None
        self._index_cur_bit = -1

    def queue_tx(self, msg: CanMessage) -> None:
        """Loads a logical message into the hardware mailbox to be sent."""
        if self._tx_buffer is None and self._state != _State.BUS_OFF:
            self._index_cur_bit = -1
            self._last_message_id = msg.id
            self._tx_buffer = CanFrame.encode_from_CanMessage(msg)
            if canSettings.DEBUG:
                print(f"{self._name}: ",self._tx_buffer, msg.data)

    def reset_state(self) -> None:
        self._tec = self._rec = 0
        self._review_current_state()

    def get_error_state(self) -> _State:
        return self._state

    def get_full_message(self) -> CanMessage | None:
        msg = None
        if self._last_message:
            id, data, _ = CanFrame.decode_message_bytearray(self._last_message)
            msg = CanMessage(id, data)
            self._last_message = None
        return msg

    def get_last_message_id(self) -> int:
        return self._last_message_id

    def get_next_bit(self) -> int:
        """Called every tick to get the controller's driven voltage.

        Returns:
            0 (Dominant), 1 (Recessive).
        """
        if self._error_buffer:
            return self._error_buffer[0]

        self._bit_since_last_msg += 1

        if not self._tx_buffer or self._state == _State.BUS_OFF:
            return 1

        if self._state == _State.ERROR_PASSIVE and self._bit_since_last_msg < 8:
            return 1

        self._index_cur_bit += 1

        if self._index_cur_bit == len(self._tx_buffer):
            self.clear_tx_buffer()
            return 1

        assert self._index_cur_bit >= 0, "Current bit < 0"
        if canSettings.DEBUG:
            print (f"{self._name}'s curbit:",
                   self._index_cur_bit,
                   self._tx_buffer[self._index_cur_bit],
                   "| # bits since last message:",
                   self._bit_since_last_msg
                   )
        return self._tx_buffer[self._index_cur_bit]

    def _process_received_bit_on_receival_ecu(self, bit):
        self._bit_since_last_msg += 1
        if not self._rx_buffer and bit == 1:
            # First bit of a message has to be 0
            return
        if CanFrame._is_message_complete(self._rx_buffer):
            self._bit_since_last_msg = 0
            self._last_message = self._rx_buffer
            self._rec = max(0, self._rec - 1)
            self._review_current_state()
            self.clear_rx_buffer()
            return

        self._rx_buffer.append(bit)

        if canSettings.DEBUG:
            print(self._rx_buffer)
        if (
                CanFrame.is_bit_stuffing_wrong(self._rx_buffer) or
                CanFrame.is_form_error(self._rx_buffer) or
                CanFrame.is_crc_error(self._rx_buffer)
        ):
            if canSettings.DEBUG:
                if CanFrame.is_bit_stuffing_wrong(self._rx_buffer):
                    print(f"{self._name} Bit Stuffing error")
                if CanFrame.is_form_error(self._rx_buffer):
                    print(f"{self._name} Form error")
                if CanFrame.is_crc_error(self._rx_buffer):
                    print(f"{self._name} CRC error")
                print(f"{self._name}:",self._rx_buffer)
            self._raise_error(sending = False)

    def _raise_error(self, sending: bool = True) -> None:
        self._review_current_state()

        if self._state == _State.BUS_OFF:
            self._error_buffer = None
        elif self._state == _State.ERROR_PASSIVE:
            self._error_buffer = deque([1] * 6 + [1] * 8)
        else:
            self._error_buffer = deque([0] * 6 + [1] * 8) 

        if sending:
            self.clear_tx_buffer()
            self._tec = min(self._tec + 8, 255)
        else:
            self.clear_rx_buffer()
            self._rec = min(self._rec + 1, 255)


    def _review_current_state(self) -> None:
        if self._tec >= 255:
            self._state = _State.BUS_OFF
        elif self._rec >= 128 or self._tec >= 128:
            self._state = _State.ERROR_PASSIVE
        else:
            self._state = _State.ERROR_ACTIVE

    def process_received_bit(self, bit: int) -> bool:
        """Called every tick to process the actual bus voltage.

        Returns:
            True if message is finished (_index_cur_bit = len(_tx_buffer) -1)
            False otherwise
        """
        # TODO:
        #   - Implement ACK.
        #   - Implement CRC.
        #   - Implement Reception-only errors

        if canSettings.DEBUG:
            print(f"{self._name}: ",self._state, self._tec, self._rec)

        if self._error_buffer:
            self._bit_since_last_msg = 0
            cur_err_bit = self._error_buffer.popleft()
            if cur_err_bit == 1 and bit == 0:
                if self._state == _State.ERROR_PASSIVE and len(self._error_buffer) < 8:
                    self._error_buffer.extend([1] * 8)
                else:
                    self._error_buffer.append(1)
            if canSettings.DEBUG:
                print(f"{self._name} ERROR BUFFER")
                print(f"{self._name}: ",self._error_buffer)
            return False

        if not self._tx_buffer:
            self._process_received_bit_on_receival_ecu(bit)
            if canSettings.DEBUG:
                print(f"{self._name} Receiving")
            return False

        if canSettings.DEBUG:
            print(f"{self._name} Sending")
            print(self._tx_buffer)
            print(self._index_cur_bit)


        cur_msg = deque(list(self._tx_buffer)[:self._index_cur_bit])

        if (
                # (bit == 1 and CanFrame.is_bit_ack(cur_msg, self._index_cur_bit)) or
                CanFrame.is_bit_stuffing_wrong(cur_msg) or
                CanFrame.is_form_error(cur_msg) or
                CanFrame.is_crc_error(cur_msg)
        ):
            if canSettings.DEBUG:
                if CanFrame.is_bit_stuffing_wrong(cur_msg):
                    print(f"{self._name} Bit Stuffing error")
                if CanFrame.is_form_error(cur_msg):
                    print(f"{self._name} Form error")
                if CanFrame.is_crc_error(cur_msg):
                    print(f"{self._name} CRC error")
                print(f"{self._name}",cur_msg)
            self._raise_error()
            return False

        if bit != self._tx_buffer[self._index_cur_bit]:
            if CanFrame.is_bit_arbitration(self._tx_buffer, self._index_cur_bit):
                # Lost arbitration
                if canSettings.DEBUG:
                    print("Stop sending. Cur index:", self._index_cur_bit, "\nSent vs Rec:", self._tx_buffer[self._index_cur_bit], bit)

                self._rx_buffer = deque(list(self._tx_buffer)[:self._index_cur_bit])
                self._rx_buffer.append(bit)
                self.clear_tx_buffer()
            else:
                self._raise_error()
            return False

        if self._index_cur_bit == len(self._tx_buffer) - 1:
            self._bit_since_last_msg = 0
            self._tec = max(0, self._tec - 1)
            self._review_current_state()
            self.clear_tx_buffer()
            return True

        return False


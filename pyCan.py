""" TODO
    - isIdle better in Canbus or Ecu?
    - Ecu automatic retransmission upon error
    - auto_retransmission in Ecu or CanController?
    - check if the callbacks are enough
    - is CanMessage necessary?
"""

from dataclasses import dataclass
from typing import Callable

@dataclass
class CanMessage:
    """A logical CAN message representation."""
    id: int
    data: bytearray


class CanController:
    """A class used to model the low-level CAN hardware.

    This class enforces the physical rules of the CAN protocol, maintains the
    Error Counters (TEC, REC), and handles bit-level state machines. It
    exposes valid hardware registers to the software (Ecu).

    Attributes:
        name (str): The name of the controller for debugging.
        auto_retransmit (bool): Hardware register to toggle automatic retries.
    """

    def __init__(self, name: str):
        self._name = name
        self._tec = 0
        self._rec = 0

        # Valid Hardware Registers an attacker can manipulate
        self.auto_retransmit = True

        self._tx_mailbox: CanMessage | None = None

        # Callbacks triggered to wake up the ECU software
        self._on_rx_callback = lambda msg: None
        self._on_tx_error_callback = lambda: None

    def bind_callbacks(self, on_rx: Callable, on_tx_error: Callable) -> None:
        """Binds the hardware interrupts to the ECU software routines."""
        self._on_rx_callback = on_rx
        self._on_tx_error_callback = on_tx_error

    # --- Hardware Registers (Software API) ---
    def set_auto_retransmit(self, enabled: bool) -> None:
        """Hardware register to enable/disable automatic retransmissions."""
        self.auto_retransmit = enabled

    def clear_tx_buffer(self) -> None:
        """Flushes the hardware transmit mailbox."""
        self._tx_mailbox = None

    def queue_tx(self, message: CanMessage) -> None:
        """Loads a logical message into the hardware mailbox to be sent."""
        if self._tx_mailbox is None:
            self._tx_mailbox = message

    # --- Bit-Level Physics Engine ---
    def get_next_bit(self) -> int | None:
        """Called every tick to get the controller's driven voltage.

        Returns:
            0 (Dominant), 1 (Recessive), or None (Listening).
        """
        # TODO: Implement state machine (IDLE, ARBITRATION, DATA, etc.)
        # TODO: Implement WeepingCAN injection logic here based on current state
        return None

    def process_received_bit(self, bit: int) -> None:
        """Called every tick to process the actual bus voltage."""
        # TODO: Implement Bit Stuffing checks and TEC/REC increments.
        # If a transmit error occurs, call self._on_tx_error_callback()
        # If a frame completes successfully, call self._on_rx_callback(completed_msg)
        pass


class Ecu:
    """A class used to model the High-Level ECU software.

    This acts as the base class for users. It completely hides the bit-level
    physics, exposing only logical software hooks like `setup` and `send`.

    Attributes:
        id (int): Logical identifier for the ECU.
        name (str): Human-readable name.
    """

    def __init__(self, ecu_id: int, name: str):
        self._id = ecu_id
        self._name = name

        # The ECU inherently owns its CanController (hardware)
        self._controller = CanController(name)
        self._controller.bind_callbacks(
                on_rx=self.on_message_received,
                on_tx_error=self.on_transmit_error
                )

    # --- Internal Bit-Level API (Called strictly by Canbus) ---
    def _get_tx_bit(self) -> int | None:
        return self._controller.get_next_bit()

    def _rx_bit(self, bit: int) -> None:
        self._controller.process_received_bit(bit)

    # --- Public API for User to Override ---
    def setup(self) -> None:
        """Called once when the simulation starts."""
        pass

    def on_message_received(self, message: CanMessage) -> None:
        """Interrupt triggered when a valid frame arrives."""
        pass

    def on_transmit_error(self) -> None:
        """Interrupt triggered if the hardware detects an error while sending."""
        pass

    def send(self, message: CanMessage) -> None:
        """High-level method to send a CAN message."""
        self._controller.queue_tx(message)


class Canbus:
    """A class used to model the CAN BUS physical layer.

    Attributes:
        baud_rate (int): frequency of bits sent every second.
        ecus (set[Ecu] | list[Ecu]): The ecus registered to this CAN BUS.
    """

    def __init__(self, baud_rate: int, ecus: set[Ecu] | list[Ecu]):
        self._current_bit = 1
        self._baud_rate = baud_rate

        for ecu in ecus:
            assert isinstance(ecu, Ecu), ("A list (set) of ecus was expected, " +
                                          "but at least one item was not an Ecu")
        self._ecus = set(ecus)

    def startSimulation(self) -> None:
        """Start the can tick action cycle.

        Starts the endless bit cycle loop that, firstly updates the current bit
        value, then sends the updated value to every ecu. To terminate the loop
        use the CTRL+C keyboard shortcut.
        """
        print("Initializing ECUs...")
        for ecu in self._ecus:
            ecu.setup()

        try:
            while True:
                self._update_current_bit()
                self._send_updated_bit_value_to_ecus()

                self._current_bit = 1 
        except KeyboardInterrupt:
            print("Exiting...")
            return

    def _update_current_bit(self) -> None:
        """Update the current bit.

        Computes the wiredAND and updates the bus value by iterating over
        the registered ecus and retrieving the value they want to send.
        """
        for ecu in self._ecus:
            received = ecu._get_tx_bit()
            if received is None:
                continue

            assert received in [0, 1], f"Expected 0 or 1. Received {received}."
            self._current_bit &= received

    def _send_updated_bit_value_to_ecus(self) -> None:
        """Propagate the current bit to the ecus.

        Sends the newly computed bit value to all the registered ecus.
        """
        for ecu in self._ecus:
            ecu._rx_bit(self._current_bit)


# ==========================================
# USER IMPLEMENTATION EXAMPLE
# ==========================================

class BusOffEcu(Ecu):
    """An ECU implementing the WeepingCAN attack."""

    def __init__(self, ecu_id: int, name: str, victim_id: int):
        super().__init__(ecu_id, name)
        self.victim_id = victim_id
        self.attack_counter = 0

    def setup(self) -> None:
        """Runs once at boot. Disables retransmission to stay stealthy."""
        self._controller.set_auto_retransmit(False)

    def on_message_received(self, message: CanMessage) -> None:
        """Tracks the bus to execute the skipping attack strategy."""
        if message.id == self.victim_id:
            self.attack_counter += 1

            if self.attack_counter % 3 == 0: 
                # Create attack message
                attack_msg = CanMessage(id=self.victim_id, data=bytearray([0xFF])) 
                self.send(attack_msg)

    def on_transmit_error(self) -> None:
        """Alternatively, we can abort the transmission upon error."""
        self._controller.clear_tx_buffer()


if __name__ == "__main__":
    print("TESTING BUS ARCHITECTURE")

    normal_ecu = Ecu(ecu_id=1, name="Brakes")
    attacker_ecu = BusOffEcu(ecu_id=99, name="Attacker", victim_id=0x100)

    ecus = {normal_ecu, attacker_ecu}

    bus = Canbus(baud_rate=500000, ecus=ecus)
    # bus.startSimulation()
    print("Architecture verified.")

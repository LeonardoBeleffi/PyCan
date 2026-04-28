from canMessage import CanMessage
from typing import Callable

class _CanController:
    """A class used to model the low-level CAN hardware.

    This class enforces the physical rules of the CAN protocol, maintains the
    Error Counters (TEC, REC), and handles bit-level state machines. It
    exposes valid hardware registers to the software (Ecu).

    Attributes:
        auto_retransmit (bool): Hardware register to toggle automatic retries.
    """

    def __init__(self, auto_retransmit: bool = True):
        self._tec = 0
        self._rec = 0

        # Valid Hardware Registers an attacker can manipulate
        self._auto_retransmit = auto_retransmit

        self._tx_mailbox: CanMessage | None = None

        # Callbacks triggered to wake up the ECU software
        self._on_rx_callback = lambda msg: None
        self._on_tx_error_callback = lambda: None

    def bind_callbacks(self, on_rx: Callable, on_tx_error: Callable) -> None:
        """Binds the hardware interrupts to the ECU software routines."""
        self._on_rx_callback = on_rx
        self._on_tx_error_callback = on_tx_error

    # --- Hardware Registers (Software API) ---
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



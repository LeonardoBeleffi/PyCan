from canController import _CanController
from canMessage import CanMessage

class Ecu:
    """A class used to model the High-Level ECU software.

    This acts as the base class for users. It completely hides the bit-level
    physics, exposing only logical software hooks like `setup` and `send`.

    Attributes:
        id (int): Logical identifier for the ECU.
        name (str): Human-readable name.
        auto_retransmit (bool): Hardware register to toggle automatic retries.
    """

    def __init__(self, ecu_id: int, name: str, auto_retransmit: bool = True):
        self._id = ecu_id
        self._name = name

        # The ECU inherently owns its _CanController (hardware)
        self._controller = _CanController(name, auto_retransmit = auto_retransmit)
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



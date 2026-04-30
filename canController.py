from canMessage import CanMessage
from typing import Callable
from collections import deque

class _MessageUtilities:
    """TODO:
            - implement bit stuffing
            - implement extended format
            - implement decent CRC algorithm
    """

    def __init__(self, id: int, data: bytearray):
        self._id = id
        self._data = data
        self._ide = False

    def set_extended_format(self, is_extended: bool) -> self:
        assert is_extended is False, "Extended Format not supported"
        self._ide = is_extended

    def add_bit_stuffing(self, msg: deque[int]) -> deque[int]:
        # TODO: implement
        return msg
    
    def remove_bit_stuffing(self, msg: deque[int]) -> deque[int]:
        # TODO: implement
        return msg

    def _compute_crc(self, msg: deque[int]) -> list[int]:
        # TODO: implement
        return [1] * 15

    def encode_message_binary(self) -> deque[int]:
        msg = deque()
        # SoF
        msg.append(0)
        # Arbitration ID
        msg.extend([1 if b == "1" else 0 for b in f"{self._id:011b}"])
        # RTR
        msg.append(0)
        # IDE
        msg.append(1 if self._ide else 0)
        # R0
        msg.append(0)
        # DLC
        l = len(self._data)
        assert l <= 8, "Message too long"
        msg.extend([1 if b == "1" else 0 for b in f"{l:04b}"])
        # Data
        msg.extend([1 if b == "1" else 0
                    for b in "".join([f"{byte:08b}" for byte in self._data])])
        # CRC
        msg.extend(self._compute_crc(msg))
        # CRC del
        msg.append(1)
        # ACK
        msg.append(1)
        # ACK del
        msg.append(1)
        # EOF
        msg.extend([1] * 7)
        # IFS
        msg.extend([1] * 3)

        return add_bit_stuffing(msg)

    def _data_from_bits(self, bits: list[int]) -> bytearray:
        return bytearray(
            sum(b << (7 - i) for i, b in enumerate(bits[j:j+8]))
            for j in range(0, len(bits), 8)
        )

    def decode_message_bytearray(self, msg: deque[int]) -> tuple[int, bytearray]:
        msg = self.remove_bit_stuffing(msg)
        bkp = list(msg)

        assert False, "Not implemented"
        assert msg.popleft() == 1, "Error in SOF"
        # Arbitration ID (11 bits)
        id = int(''.join([f'{msg.popleft()}' for _ in range(11)]), 2)
        assert msg.popleft() == 0, "RTR messages not supported yet"
        assert msg.popleft() == 0, "Extended Frames not supported yet"
        # r0
        _ = msg.popleft()
        length = int(''.join([f'{msg.popleft()}' for _ in range(4)]), 2)
        data = _data_from_bits([msg.popleft() for _ in range(8 * length)])
        assert [msg.popleft() for _ in range(15)] == self._compute_crc(bkp[:-28]), "Error in CRC"
        assert msg.popleft() == 1, "Error in CRC delimiter"
        # ACK
        msg.popleft()
        assert msg.popleft() == 1, "Error in ACK delimiter"
        assert 0 not in [msg.popleft() for _ in range(7)], "Error in EOF"
        assert 0 not in [msg.popleft() for _ in range(3)], "Error in IFS"
        assert len(msg) == 0, "Error in msg length"

        return id, data

    @staticmethod
    def is_arbitration(msg: deque[int], index: int):
        assert False, "Not implemented"

    @staticmethod
    def is_ack(msg: deque[int], index: int):
        assert False, "Not implemented"

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

        self._tx_mailbox: deque[int] | None = None
        self._index_cur_bit = -1

        # Callbacks triggered to wake up the ECU software
        self._on_rx_callback = lambda msg: None
        self._on_tx_error_callback = lambda: None
        
        self._last_bit_success = False
        self._last_message_sent = False

    """TODO: maybe remove"""
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
            self._tx_mailbox = _MessageUtilities(message.id, message.data)
                                .encode_message_binary()

    # --- Bit-Level Physics Engine ---
    def get_next_bit(self) -> int | None:
        """Called every tick to get the controller's driven voltage.

        Returns:
            0 (Dominant), 1 (Recessive), or None (Listening).
        """
        # TODO: Implement state machine (IDLE, ARBITRATION, DATA, etc.)
        # TODO: Implement WeepingCAN injection logic here based on current state
        if not self._tx_mailbox:
            return None
        self._index_cur_bit += 1
        assert self._index_cur_bit >= 0, "Current bit < 0"
        assert self._index_cur_bit < len(self._tx_mailbox),
                "Current bit > msg len"
        return self._tx_mailbox[self._index_cur_bit]

    def process_received_bit(self, bit: int) -> bool:
        """Called every tick to process the actual bus voltage.

        Returns:
            True if bit was sent correctly and transmittion can continue,
            False if some error occurred and trasmittion needs to stop
        """
        # TODO: Implement and TEC/REC increments.
        # If a transmit error occurs, call self._on_tx_error_callback()
        # If a frame completes successfully, call self._on_rx_callback(completed_msg)
        if bit == self._tx_mailbox[self._index_cur_bit]:
            return True

        # check if is error
        if _MessageUtilities.is_error(self._tx_mailbox, self._index_cur_bit):
            return True

        if _MessageUtilities.is_arbitration(self._tx_mailbox, self._index_cur_bit):
            self._last_message_sent = False
            return False

        if _MessageUtilities.is_ack(self._tx_mailbox, self._index_cur_bit):
            return True

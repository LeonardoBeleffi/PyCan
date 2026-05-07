from canMessage import CanMessage
from typing import Callable
from collections import deque
from enum import Enum

class CanFrame:
    """TODO:
            - implement bit stuffing
            - implement extended format
            - implement decent CRC algorithm
    """

    def __init__(self, id: int, data: bytearray):
        self._id = id
        self._data = data
        self._ide = False

    def set_extended_format(self, is_extended: bool):
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

        return self.add_bit_stuffing(msg)

    def _data_from_bits(self, bits: list[int]) -> bytearray:
        return bytearray(
            sum(b << (7 - i) for i, b in enumerate(bits[j:j+8]))
            for j in range(0, len(bits), 8)
        )

    # TODO implement
    @staticmethod
    def is_message_complete(msg:deque[int]) -> bool:
        it = iter(msg)
        last = None
        run = 0

        def next_destuffed():
            nonlocal last, run

            try:
                b = next(it)
            except StopIteration:
                return None

            if b == last:
                run += 1
            else:
                last = b
                run = 1

            if run == 5:
                try:
                    stuffed = next(it)
                except StopIteration:
                    return None

                if stuffed == last:
                    # invalid stuffing → but message is still "complete"
                    # completeness ≠ correctness
                    return None

                last = None
                run = 0

            return b

        # --- parse until CRC end (destuffed) ---

        # SOF
        if next_destuffed() is None:
            return False

        # ID A
        for _ in range(11):
            if next_destuffed() is None:
                return False

        # RTR/SRR
        if next_destuffed() is None:
            return False

        # IDE
        ide = next_destuffed()
        if ide is None:
            return False

        if ide == 0:
            # r0
            if next_destuffed() is None:
                return False

            # DLC
            dlc_bits = []
            for _ in range(4):
                b = next_destuffed()
                if b is None:
                    return False
                dlc_bits.append(b)

        else:
            # ID B
            for _ in range(18):
                if next_destuffed() is None:
                    return False

            # RTR
            if next_destuffed() is None:
                return False

            # r1, r0
            for _ in range(2):
                if next_destuffed() is None:
                    return False

            # DLC
            dlc_bits = []
            for _ in range(4):
                b = next_destuffed()
                if b is None:
                    return False
                dlc_bits.append(b)

        # DLC value
        dlc = 0
        for b in dlc_bits:
            dlc = (dlc << 1) | b

        # DATA
        for _ in range(8 * dlc):
            if next_destuffed() is None:
                return False

        # CRC (15 bits)
        for _ in range(15):
            if next_destuffed() is None:
                return False

        # --- now remaining bits are NOT stuffed ---

        # Need 13 bits:
        # CRC del (1) + ACK (1) + ACK del (1) + EOF (7) + IFS (3)
        remaining = list(it)

        return len(remaining) >= 13

    @staticmethod
    def decode_message_bytearray(msg: deque[int]) -> tuple[int, bytearray, bool]:
        msg = CanFrame.destuff(msg)
        bkp = list(msg)

        assert False, "Not implemented"
        assert msg.popleft() == 1, "Error in SOF"
        # Arbitration ID (11 bits)
        id = int(''.join([f'{msg.popleft()}' for _ in range(11)]), 2)
        assert msg.popleft() == 0, "RTR messages not supported yet"
        ide = msg.popleft()
        assert ide == 0, "Extended Frames not supported yet"
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

        return id, data, ide

    @staticmethod
    def encode_from_CanMessage(msg: CanMessage) -> deque[int]:
        return CanFrame(msg.id, msg.data).encode_message_binary()

    @staticmethod
    def is_frame_extended(msg: deque[int]) -> bool:
        assert len(msg) > 13, "Frame Not Valid"
        return msg[13] == 1

    @staticmethod
    def error_in_bitStuffing(msg: deque[int]) -> bool:
        assert False, "Not implemented"
        assert len(msg) > 0, "Error in msg length"

        _, data, ide = CanFrame.decode_message_bytearray(msg)
        data_len = len(data)
        if ide:
            base = 39
        else:
            base = 19
        l = base + (8 * data_len) + 15 == index
        msg = msg[:l]

        lastBit = None
        consecutive_bits = 0
        for b in msg:
            if b == lastBit:
                consecutive_bits += 1
            else:
                lastBit = b
                consecutive_bits = 1

            if consecutive_bits > 5:
                return True
        return False

    @staticmethod
    def is_bit_arbitration(msg: deque[int], index: int) -> bool:
        assert len(msg) > 13, "Frame Not Valid"
        if msg[13] == 1:
            # Extended Frame
            return index <= 32
        # Base Frame
        return index <= 12

    @staticmethod
    def is_crc_error(msg: deque[int]) -> bool:
        return False

    @staticmethod
    def destuff(bits: deque[int]) -> deque[int]:
        out = deque()
        last = None
        count = 0

        it = iter(bits)

        for b in it:
            out.append(b)

            if b == last:
                count += 1
            else:
                last = b
                count = 1

            if count == 5:
                # next bit should be stuffed (opposite)
                try:
                    stuffed = next(it)
                except StopIteration:
                    break  # incomplete → just stop cleanly

                # skip stuffed bit (do NOT append it)
                last = None
                count = 0

        return out

    @staticmethod
    def is_form_error(msg: deque[int]) -> bool:
        bits = list(CanFrame.destuff(msg))

        # need at least enough to read DLC
        if len(bits) < 19:
            return False

        # detect format
        ide = bits[13]  # 0=std, 1=extended

        if ide == 0:
            base = 19
            dlc_bits = bits[15:19]
        else:
            if len(bits) < 39:
                return False
            base = 39
            dlc_bits = bits[35:39]

        dlc = int("".join(str(b) for b in dlc_bits), 2)

        # compute key indices
        crc_end = base + (8 * dlc) + 14
        crc_del = crc_end + 1
        ack     = crc_del + 1
        ack_del = ack + 1
        eof_start = ack_del + 1
        eof_end = eof_start + 7
        ifs_start = eof_end
        ifs_end   = ifs_start + 3

        # check only if bits are present

        # CRC delimiter
        if len(bits) > crc_del and bits[crc_del] != 1:
            return True

        # ACK delimiter
        if len(bits) > ack_del and bits[ack_del] != 1:
            return True

        # EOF (all must be 1)
        if len(bits) >= eof_end:
            if any(b != 1 for b in bits[eof_start:eof_end]):
                return True

        # IFS (3 recessive bits)
        if len(bits) >= ifs_end:
            if any(b != 1 for b in bits[ifs_start:ifs_end]):
                return True

        return False

    @staticmethod
    def is_bit_ack(msg: deque[int], index: int) -> bool:
        # TODO: not working
        return False
        _, data, ide = CanFrame.decode_message_bytearray(msg)
        data_len = len(data)
        if ide:
            base = 39
        else:
            base = 19
        return base + (8 * data_len) + 16 == index

    @staticmethod
    def is_bit_stuffing_wrong(msg: deque[int]) -> bool:
        return False
        last = None
        count = 0

        it = iter(msg)

        for b in it:
            if b == last:
                count += 1
            else:
                last = b
                count = 1

            if count == 5:
                # next bit must exist and be opposite
                try:
                    nxt = next(it)
                except StopIteration:
                    # incomplete → cannot conclude error
                    return False

                if nxt == last:
                    # violation: same bit instead of stuffed opposite
                    return True

                # stuffed bit is correct → reset sequence
                last = None
                count = 0

        return False

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
        auto_retransmit (bool): Hardware register to toggle automatic retries.

    TODO:
        - implement error check in reading
        - implement error frame sending
        - implement ack signaling
    """

    def __init__(self):
        self._last_message_id = False
        self._receiving_frame = False
        self._last_message = None
        self._error_buffer = deque()

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
        self._sending = False

    def queue_tx(self, msg: CanMessage) -> None:
        """Loads a logical message into the hardware mailbox to be sent."""
        if self._tx_buffer is None:
            self._index_cur_bit = -1
            self._sending = True
            self._last_message_id = msg.id
            self._tx_buffer = CanFrame.encode_from_CanMessage(msg)
            print(self._tx_buffer, msg.data)

    def reset_state(self) -> None:
        self._tec = self._rec = 0
        self._state = _State.ERROR_ACTIVE

    def get_error_state(self) -> _State:
        return self._state

    def get_last_message_id(self) -> int:
        return self._last_message_id

    def frame_error(self, error_during_tx: bool = True) -> False:
        # TODO
        return False

    def get_next_bit(self) -> int:
        """Called every tick to get the controller's driven voltage.

        Returns:
            0 (Dominant), 1 (Recessive).
        """
        if not self._tx_buffer:
            return 1
        if self._state == _State.BUS_OFF:
            return 1
        if (self._state == _State.ERROR_PASSIVE or
            self._error_buffer):
            return self._error_buffer.popleft()

        self._index_cur_bit += 1

        if self._index_cur_bit == len(self._tx_buffer):
            self.clear_tx_buffer()
            return 1
        assert self._index_cur_bit >= 0, "Current bit < 0"
        print ("curbit:",self._index_cur_bit, self._tx_buffer[self._index_cur_bit])
        return self._tx_buffer[self._index_cur_bit]

    def _process_received_bit_on_receival_ecu(self, bit):
        if not self._rx_buffer and bit == 1:
            # First bit of a message has to be 0
            return
        if CanFrame.is_message_complete(self._rx_buffer):
            self._rec = max(0, self._rec - 1)
            self._last_message = self._rx_buffer
            self.clear_rx_buffer()
            if self._tx_buffer:
                self._index_cur_bit = -1
                self._sending = True
            return

        self._rx_buffer.append(bit)

        if (
                CanFrame.is_bit_stuffing_wrong(self._rx_buffer) or
                CanFrame.is_form_error(self._rx_buffer) or
                CanFrame.is_crc_error(self._rx_buffer)
        ):
            self._raise_error_during_sending(sending = False)

    def _raise_error_during_sending(self, sending: bool = True) -> None:
        if sending:
            self.clear_tx_buffer()
            self._tec = min(self._tec + 8, 255)
        else:
            self.clear_rx_buffer()
            self._rec = min(self._rec + 1, 255)

        if self._tec >= 255:
            self._state = _State.BUS_OFF
        elif self._rec >= 128 or self._tec >= 128:
            self._state = _State.ERROR_PASSIVE
            self._error_buffer = deque([1] * 6)
        else:
            self._error_buffer = deque([0] * 6)


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

        if self._tx_buffer:
            print(self._tx_buffer)
        else:
            print("EMPTY BUFFER")
        if self._error_buffer:
            return False

        if not self._sending:
            self._process_received_bit_on_receival_ecu(bit)
            return False

        cur_msg = deque(list(self._tx_buffer)[:self._index_cur_bit])

        if (
                # (bit == 1 and CanFrame.is_bit_ack(cur_msg, self._index_cur_bit)) or
                CanFrame.is_bit_stuffing_wrong(cur_msg) or
                CanFrame.is_form_error(cur_msg) or
                CanFrame.is_crc_error(cur_msg)
        ):
            self._raise_error_during_sending()
            return False

        if bit != self._tx_buffer[self._index_cur_bit]:
            if CanFrame.is_bit_arbitration(self._tx_buffer, self._index_cur_bit):
                # Lost arbitration
                self._index_cur_bit = -1
                self._sending = False
            else:
                self._raise_error_during_sending()
            return False

        if CanFrame.is_message_complete(cur_msg):
            self._tec = max(0, self._tec - 1)
            self.clear_tx_buffer()
            return True

        return False


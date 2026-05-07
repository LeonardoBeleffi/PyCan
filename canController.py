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
        """
        Applies CAN bit stuffing to the stuffable region of a frame.

        Rule: after 5 consecutive identical bits, insert one bit of the
        opposite polarity. The inserted bit itself resets the counter.

        IMPORTANT — caller responsibility:
            Pass ONLY the stuffable region: SOF + Arbitration + Control + Data + CRC (raw, 15 bits).
            The tail (CRC delimiter, ACK, ACK delimiter, EOF, IFS) must be appended
            by the caller AFTER this method returns, as those fields are never stuffed.

        Args:
            msg: unstuffed bits of the stuffable region, left-to-right (MSB first).

        Returns:
            A new deque with stuff bits inserted. The original deque is not mutated.

        Raises:
            ValueError: if msg contains values other than 0 or 1.
        """
        if any(b not in (0, 1) for b in msg):
            raise ValueError("Message must contain only bits (0 or 1).")

        stuffed: deque[int] = deque()
        consecutive_count = 1
        last_bit = None

        for bit in msg:
            stuffed.append(bit)

            if bit == last_bit:
                consecutive_count += 1
            else:
                consecutive_count = 1
                last_bit = bit

            if consecutive_count == 5:
                stuff_bit = 1 - bit          # opposite polarity
                stuffed.append(stuff_bit)
                last_bit = stuff_bit         # stuff bit resets the run
                consecutive_count = 1        # the stuff bit itself starts a new run of 1

        return stuffed

    def remove_bit_stuffing(self, msg: deque[int]) -> deque[int]:

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

        # Apply bit-stuffing
        msg = self.add_bit_stuffing(msg)

        # CRC del
        msg.append(1)
        # ACK already done
        msg.append(0)
        # ACK del
        msg.append(1)
        # EOF
        msg.extend([1] * 7)
        # IFS
        msg.extend([1] * 3)

        return msg

    def _data_from_bits(self, bits: list[int]) -> bytearray:
        return bytearray(
            sum(b << (7 - i) for i, b in enumerate(bits[j:j+8]))
            for j in range(0, len(bits), 8)
        )

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
    def _logical_to_stuffed_index(msg: deque[int], logical_target: int) -> int:
        """
        Returns the stuffed index corresponding to a given logical (unstuffed)
        bit position. Stuff bits are skipped and do not count toward logical_target.
    
        Returns -1 if the logical position is not reached (message too short).
        """
        logical_count = 0
        consecutive   = 1
        last_bit      = None
        expect_stuff  = False
    
        for stuffed_idx, bit in enumerate(msg):
            if expect_stuff:
                # This is a stuff bit — skip it logically, but still track the run
                expect_stuff = False
                last_bit     = bit
                consecutive  = 1
                continue
    
            if logical_count == logical_target:
                return stuffed_idx
    
            logical_count += 1
    
            if bit == last_bit:
                consecutive += 1
            else:
                consecutive = 1
                last_bit    = bit
    
            if consecutive == 5:
                expect_stuff = True
    
        return -1  # logical_target beyond the message
    
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
        """
        Returns True if `index` (position in the STUFFED message) falls within
        the arbitration field of the frame.
    
        Arbitration field:
            Base frame     — SOF + 11-bit ID + RTR         → logical indices 0-12
            Extended frame — SOF + 11-bit ID + SRR + IDE
                               + 18-bit ext. ID + RTR      → logical indices 0-32
    
        The IDE bit sits at logical index 13 in both frame types:
            Base frame:     IDE = 0 (dominant)
            Extended frame: IDE = 1 (recessive)
        """
        ide_stuffed_pos = CanFrame._logical_to_stuffed_index(msg, 13)
        assert ide_stuffed_pos != -1, "Frame too short to determine type (IDE bit not reached)"
    
        if msg[ide_stuffed_pos] == 1:
            # Extended frame — arbitration ends at logical index 32
            arb_end = CanFrame._logical_to_stuffed_index(msg, 32)
        else:
            # Base frame — arbitration ends at logical index 12
            arb_end = CanFrame._logical_to_stuffed_index(msg, 12)
    
        assert arb_end != -1, "Frame too short to contain full arbitration field"
        return index <= arb_end

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
    def _destuff_and_split(msg: deque[int]) -> list[int]:
        """
        Returns a logical bit list where:
          - the stuffable region (SOF → CRC) has been destuffed, and
          - the fixed tail (CRC delimiter onward) is appended as-is.
    
        This is the correct input for any function that works on logical
        (unstuffed) indices, because the tail is never stuffed and must
        not be processed by the destuffing logic.
        """
        logical_bits:            list[int]       = []
        stuffable_limit_logical: int | None      = None
        stuffable_limit_stuffed: int | None      = None
        consecutive:             int             = 1
        last_bit:                int | None      = None
        expect_stuff:            bool            = False
    
        for stuffed_idx, bit in enumerate(msg):
    
            # Once we know the stuffable boundary in stuffed-space, stop destuffing
            if stuffable_limit_stuffed is not None and stuffed_idx >= stuffable_limit_stuffed:
                # Append the remainder of the message (tail) raw, then exit
                logical_bits += list(msg)[stuffed_idx:]
                return logical_bits
    
            if expect_stuff:
                # Stuff bit: drop from logical stream, reset run
                expect_stuff = False
                last_bit     = bit
                consecutive  = 1
                continue
    
            logical_bits.append(bit)
    
            if bit == last_bit:
                consecutive += 1
            else:
                consecutive = 1
                last_bit    = bit
    
            if consecutive == 5:
                expect_stuff = True
    
            # Try to resolve the stuffable region boundary
            if stuffable_limit_logical is None:
                stuffable_limit_logical = CanFrame._try_get_stuffable_region_limit(logical_bits)
                if stuffable_limit_logical is not None:
                    # Convert the logical limit to its stuffed index so we know
                    # exactly where to stop the destuffing walk above
                    stuffable_limit_stuffed = CanFrame._logical_to_stuffed_index(
                        msg, stuffable_limit_logical
                    )
    
        return logical_bits  # Message incomplete — return what we have
    
    
    @staticmethod
    def is_form_error(msg: deque[int]) -> bool:
        bits = CanFrame._destuff_and_split(msg)  # ← only change to the original
    
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
        crc_end   = base + (8 * dlc) + 14
        crc_del   = crc_end + 1
        ack       = crc_del + 1
        ack_del   = ack + 1
        eof_start = ack_del + 1
        eof_end   = eof_start + 7
        ifs_start = eof_end
        ifs_end   = ifs_start + 3
        # check only if bits are present
        # CRC delimiter
        if len(bits) > crc_del and bits[crc_del] != 1:
            print("err crc")
            return True
        # ACK delimiter
        if len(bits) > ack_del and bits[ack_del] != 1:
            print("err ack")
            return True
        # EOF (all must be 1)
        if len(bits) >= eof_end:
            if any(b != 1 for b in bits[eof_start:eof_end]):
                print("err eof")
                return True
        # IFS (3 recessive bits)
        if len(bits) >= ifs_end:
            if any(b != 1 for b in bits[ifs_start:ifs_end]):
                print("err ifs")
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
    def _try_get_stuffable_region_limit(logical_bits: list[int]) -> int | None:
        """
        Given logical bits accumulated so far, attempt to determine the exclusive
        logical end index of the stuffable region (one past the last CRC bit).
        Returns None if not enough logical bits have arrived yet to determine
        the frame type and DLC.
    
        Stuffable region layout:
            Base frame:     SOF(1) + ID(11) + RTR(1) + IDE(1) + r0(1) + DLC(4)
                            + Data(8*dlc) + CRC(15)
                            → ends at logical index 34 + 8*dlc  (exclusive)
    
            Extended frame: SOF(1) + ID(11) + SRR(1) + IDE(1) + ExtID(18) + RTR(1)
                            + r1(1) + r0(1) + DLC(4) + Data(8*dlc) + CRC(15)
                            → ends at logical index 54 + 8*dlc  (exclusive)
        """
        # Need at least IDE bit (logical index 13) to determine frame type
        if len(logical_bits) < 14:
            return None
    
        is_extended = logical_bits[13] == 1
        dlc_start   = 35 if is_extended else 15
        data_start  = 39 if is_extended else 19
    
        # Need all 4 DLC bits
        if len(logical_bits) < dlc_start + 4:
            return None
    
        dlc_bits = logical_bits[dlc_start : dlc_start + 4]
        dlc      = (dlc_bits[0] << 3) | (dlc_bits[1] << 2) | (dlc_bits[2] << 1) | dlc_bits[3]
        dlc      = min(dlc, 8)  # DLC > 8 is treated as 8 per CAN spec
    
        return data_start + 8 * dlc + 15  # exclusive
    
    
    @staticmethod
    def is_bit_stuffing_wrong(msg: deque[int]) -> bool:
        """
        Returns True if a bit stuffing violation is detected in the stuffable
        region of a (possibly incomplete) CAN frame.
    
        Bit stuffing applies only to: SOF + Arbitration + Control + Data + CRC.
        The fixed tail (CRC delimiter onward) is never stuffed and is not checked.
    
        The function walks the message bit by bit, simultaneously:
          - checking for stuffing violations as they appear, and
          - parsing frame structure to know where the stuffable region ends.
    
        Returns False if no violation is found in the bits seen so far —
        this includes incomplete frames where the violation may not have
        arrived yet.
    
        Args:
            msg: stuffed bits of the full frame (may be incomplete).
    
        Raises:
            ValueError: if msg contains values other than 0 or 1.
        """
        if any(b not in (0, 1) for b in msg):
            raise ValueError("Message must contain only bits (0 or 1).")
    
        logical_bits:           list[int] = []
        consecutive:            int       = 1
        last_bit:               int | None = None
        expect_stuff:           bool      = False
        stuffable_limit_logical: int | None = None  # exclusive logical end of stuffable region
    
        for bit in msg:
            # Stop checking once we have walked past the stuffable region
            if stuffable_limit_logical is not None and len(logical_bits) >= stuffable_limit_logical:
                break
    
            if expect_stuff:
                expected_stuff_bit = 1 - last_bit
                if bit != expected_stuff_bit:
                    return True  # Stuffing violation — 6 consecutive identical bits
    
                # Valid stuff bit: drop it from logical stream, reset run counter
                expect_stuff = False
                last_bit     = bit
                consecutive  = 1
                continue
    
            # Normal (non-stuff) bit — add to logical stream
            logical_bits.append(bit)
    
            if bit == last_bit:
                consecutive += 1
            else:
                consecutive = 1
                last_bit    = bit
    
            if consecutive == 5:
                expect_stuff = True  # Next bit must be a stuff bit
    
            # Attempt to resolve the stuffable region boundary once we have enough context
            if stuffable_limit_logical is None:
                stuffable_limit_logical = CanFrame._try_get_stuffable_region_limit(logical_bits)
    
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
        if not self._sending or not self._tx_buffer:
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
        if self._index_cur_bit == len(self._tx_buffer) - 1:
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

        if not self._tx_buffer:
            print("EMPTY BUFFER")
        elif self._sending:
            print(self._tx_buffer)
        else:
            print("Not sending")

        if self._error_buffer:
            print("ERROR BUFFER")
            return False

        if not self._sending:
            self._process_received_bit_on_receival_ecu(bit)
            print("Receiving")
            return False

        print("Sending")
        cur_msg = deque(list(self._tx_buffer)[:self._index_cur_bit])

        if (
                # (bit == 1 and CanFrame.is_bit_ack(cur_msg, self._index_cur_bit)) or
                CanFrame.is_bit_stuffing_wrong(cur_msg) or
                CanFrame.is_form_error(cur_msg) or
                CanFrame.is_crc_error(cur_msg)
        ):
            if CanFrame.is_bit_stuffing_wrong(cur_msg):
                print("Bit Stuffing error")
                print(cur_msg)
            if CanFrame.is_form_error(cur_msg):
                print("Form error")
            if CanFrame.is_crc_error(cur_msg):
                print("CRC error")
            print(cur_msg)
            self._raise_error_during_sending()
            return False

        if bit != self._tx_buffer[self._index_cur_bit]:
            if CanFrame.is_bit_arbitration(self._tx_buffer, self._index_cur_bit):
                # Lost arbitration
                print("Stop sending. Cur index:", self._index_cur_bit, "\nSent vs Rec:", self._tx_buffer[self._index_cur_bit], bit)
                self._index_cur_bit = -1
                self._sending = False
            else:
                self._raise_error_during_sending()
            return False

        if self._index_cur_bit == len(self._tx_buffer) - 1:
            self._tec = max(0, self._tec - 1)
            self.clear_tx_buffer()
            return True

        return False


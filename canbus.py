from ecu import Ecu
from collections import deque
import time

class Canbus:
    """A class used to model the CAN BUS physical layer.

    Attributes:
        sleep_us (int): microseconds of sleep between each iteration.
        ecus (list[Ecu]): The ecus registered to this CAN BUS.
    """

    def __init__(self, sleep_us: int, ecus: list[Ecu]):
        self._sleep_us = sleep_us
        self._last_bits = deque([1 for i in range(11)])

        for ecu in ecus:
            assert isinstance(ecu, Ecu), ("A list of ecus was expected, but " +
                                          "at least one item was not an Ecu")
        self._ecus = set(ecus)

    def isIdle(self) -> bool:
        """Bus Idle condition check

        Returns:
            True if the bus is idle (last 11 bits = 1)
            False otherwise
        """
        return 0 in self._last_bits

    def startSimulation(self) -> None:
        """Start the can tick action cycle.

        Starts the endless bit cycle loop that, firstly updates the current bit
        value, then sends the updated value to every ecu. To terminate the loop
        use the CTRL+C keyboard shortcut.
        """
        try:
            while True:
                self._last_bits.popleft()
                self._last_bits.append(1)

                self._update_ecus_time()
                self._update_current_bit()
                self._send_updated_bit_value_to_ecus()

                time.sleep(self._sleep_us/1_000_000.0)

        except KeyboardInterrupt:
            print("Exiting...")
            return

    def _update_ecus_time(self) -> None:
        """Propagate the progression of time to all ecus"""
        for ecu in self._ecus:
            ecu.advance_time()

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
            self._last_bits[-1] &= received

    def _send_updated_bit_value_to_ecus(self) -> None:
        """Propagate the current bit to the ecus.

        Sends the newly computed bit value to all the registered ecus.
        """
        for ecu in self._ecus:
            ecu._rx_bit(self._last_bits[-1])


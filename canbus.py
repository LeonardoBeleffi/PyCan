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
        self.IDLE_COUNTER_THRESHOLD = 11
        self.__idle_counter = self.IDLE_COUNTER_THRESHOLD
        self.last_bit = 1

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
        return self.__idle_counter >= self.IDLE_COUNTER_THRESHOLD

    def startSimulation(self) -> None:
        """Start the can tick action cycle.

        Starts the endless bit cycle loop that, firstly updates the current bit
        value, then sends the updated value to every ecu. To terminate the loop
        use the CTRL+C keyboard shortcut.
        """
        try:
            while True:

                self.update_ecus_time()
                self.__update_current_bit()
                self._send_updated_bit_value_to_ecus()

                time.sleep(self._sleep_us/1_000.0)

        except KeyboardInterrupt:
            print("Exiting...")
            return

    def update_ecus_time(self) -> None:
        """Propagate the progression of time to all ecus"""
        for ecu in self._ecus:
            ecu.increase_time()

    def __update_current_bit(self) -> None:
        """Update the current bit.

        Computes the wiredAND and updates the bus value by iterating over
        the registered ecus and retrieving the value they want to send.
        """
        self.last_bit = 1
        for ecu in self._ecus:
            ecu.check_message_transmission(self.isIdle())
            received = ecu.get_tx_bit()

            assert received in [0, 1], f"Expected 0 or 1. Received {received}."
            self.last_bit &= received

        # manage 1s counter for idle state
        if self.last_bit == 1:
            self.__idle_counter += 1
        else:
            self.__idle_counter = 0
        print(self.__idle_counter, self.isIdle())

    def _send_updated_bit_value_to_ecus(self) -> None:
        """Propagate the current bit to the ecus.

        Sends the newly computed bit value to all the registered ecus.
        """
        for ecu in self._ecus:
            ecu.rx_bit(self.last_bit)


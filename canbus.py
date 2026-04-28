from ecu import Ecu

class Canbus:
    """A class used to model the CAN BUS physical layer.

    Attributes:
        baud_rate (int): frequency of bits sent every second.
        ecus (list[Ecu]): The ecus registered to this CAN BUS.
    """

    def __init__(self, baud_rate: int, ecus: list[Ecu]):
        self._current_bit = 1
        self._baud_rate = baud_rate

        for ecu in ecus:
            assert isinstance(ecu, Ecu), ("A list of ecus was expected, but " +
                                          "at least one item was not an Ecu")
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


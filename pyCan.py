""" TODO
    - isIdle better in Canbus or Ecu?
    - Ecu automatic retransmission upon error
"""

class Canbus:
    """A class used to model the CAN BUS.

    Attributes:
        baud_rate (int): frequency of bits sent every second.
        ecus (set[ecu] or list[ecu]): The ecus registered to this CAN BUS.
    """

    def __init__(self, baud_rate: int, ecus: set[ecu] | list[ecu]):
        self._current_bit = 1
        self._baud_rate = baud_rate
        for ecu in ecus:
            print(type(ecu))
            assert type(ecu) == Ecu, ("A list (set) of ecus was expected, " +
                                      "but at least one item was not an ecu")
        self._ecus = set(ecus)

    def startSimulation(self) -> None:
        """Start the can tick action cycle.

        Starts the endless bit cicle loop that, firstly updates the current bit
        value, then sends the updated value to every ecu. To terminate the loop
        use the CTRL+C keyboard shortcut.
        """

        try:
            while True:
                self._get_new_bit_value_from_ecu()
                self._send_updated_bit_value_to_ecus()
                self._current_bit = 1
        except KeyboardInterrupt:
            print("Exiting...")
            return

    def _update_current_bit(self):
        """Update the current bit.

        Computes the wiredAND and updates the bus_value value by iterating over
        the registered ecus and then retrieving the value those ecus want to
        send.
        """

        for ecu in self._ecus:
            received = ecu.sendValue()
            if received == None:
                continue

            assert received == 0 or received == 1, ("0 or 1 expected, " +
                                                    f"but {received} received")
            self._current_bit &= received


    def _send_updated_bit_value_to_ecus(self):
        """Propagate the current bit to the ecus.

        Sends the newly computed bit value to all the registered ecus.
        """

        for ecu in self._ecus:
            ecu.receiveValue(self._current_bit)


class Ecu:
    def __init__(self, bus, id: int, name: str) -> Ecu:
        self._bus = bus
        self._id = id
        self._name = name

    def getValueToSend(self) -> None:
        assert False, "TODO: implement"

    def setValueToSend(self) -> None:
        assert False, "TODO: implement"



if __name__ == "__main__":
    print("TEST")
    a = Canbus(100)
    a.startSimulation()
    a.addEcus({Ecu(a, 1, "pippo")})


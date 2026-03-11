class Canbus:
    def __init__(self, baud_rate: int):
        self._current_bit = 1
        self._baud_rate = baud_rate
        self._ecus = set()

    def addEcus(self, ecus: set[ecu] | list[ecu]):
        print(type(ecus))
        for ecu in ecus:
            print(type(ecu))
            assert type(ecu) == Ecu, ("A list (set) of ecus was expected, " +
                                      "but at least one item was not an ecu")
        self._ecus |= ecus

    def isIdle(self):
        #   if not self._current_bit:
        #       return False
        assert False, "TODO: implement"

    def setValue(self):
        assert False, "TODO: implement"

    def getValue(self):
        assert False, "TODO: implement"

    def startSimulation(self):
        assert False, "TODO: implement"
        self._is_simulation_on = True
        for ecu in self._ecus:
            ecu.getValueToSend()


class Ecu:
    def __init__(self, bus, id: int, name: str) -> Ecu:
        self._bus = bus
        self._id = id
        self._name = name

    def getValueToSend(self):
        assert False, "TODO: implement"

    def setValueToSend(self):
        assert False, "TODO: implement"



if __name__ == "__main__":
    print("TEST")
    a = Canbus(100)
    a.addEcus({Ecu(a, 1, "pippo")})


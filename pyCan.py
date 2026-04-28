""" TODO
    - isIdle better in Canbus, Ecu or _CanController?
    - Ecu automatic retransmission upon error
    - auto_retransmission in Ecu or _CanController?
    - check if the callbacks are enough
    - is CanMessage necessary?
    - add Extended Frame format
"""
# __all__ = ['Canbus', 'Ecu']

# ==========================================
# USER IMPLEMENTATION EXAMPLE
# ==========================================

class BusOffEcu(Ecu):
    """An ECU implementing the WeepingCAN attack."""

    def __init__(self, ecu_id: int, name: str, victim_id: int):
        super().__init__(ecu_id, name)
        self.victim_id = victim_id
        self.attack_counter = 0

    def setup(self) -> None:
        """Runs once at boot. Disables retransmission to stay stealthy."""
        self._controller.set_auto_retransmit(False)

    def on_message_received(self, message: CanMessage) -> None:
        """Tracks the bus to execute the skipping attack strategy."""
        if message.id == self.victim_id:
            self.attack_counter += 1

            if self.attack_counter % 3 == 0: 
                # Create attack message
                attack_msg = CanMessage(id=self.victim_id, data=bytearray([0xFF])) 
                self.send(attack_msg)

    def on_transmit_error(self) -> None:
        """Alternatively, we can abort the transmission upon error."""
        self._controller.clear_tx_buffer()


if __name__ == "__main__":
    print("TESTING BUS ARCHITECTURE")

    normal_ecu = Ecu(ecu_id=1, name="Brakes")
    attacker_ecu = BusOffEcu(ecu_id=99, name="Attacker", victim_id=0x100)

    ecus = {normal_ecu, attacker_ecu}

    bus = Canbus(baud_rate=500000, ecus=ecus)
    # bus.startSimulation()
    print("Architecture verified.")

from canbus import Canbus
from ecu import Ecu, AttackerEcu
import json
import os

def load_ecus(path: str) -> list[Ecu]:
    with open(path) as f:
        return [Ecu(d["id"], d["name"], {int(k): v for k, v in d["messages"].items()}) for d in json.load(f)]
    

def load_attacker_ecus(path: str) -> list[AttackerEcu]:
    with open(path) as f:
        return [AttackerEcu(d["id"], d["name"], {int(k): v for k, v in d["messages"].items()}) for d in json.load(f)]

if __name__ == "__main__":
    
    ecus = load_ecus(os.path.join("resources","ecus.json"))

    ecus = ecus + load_attacker_ecus(os.path.join("resources","infected_ecus.json"))

    canbus = Canbus(0,ecus)
    canbus.startSimulation()

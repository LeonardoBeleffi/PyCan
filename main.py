from canbus import Canbus
from ecu import Ecu, AttackerEcu
import json
import os
import argparse
import canSettings

def load_ecus(path: str) -> list[Ecu]:
    with open(path) as f:
        return [Ecu(d["id"], d["name"], {int(k): v for k, v in d["messages"].items()}) for d in json.load(f)]


def load_attacker_ecus(path: str, skip_attack: int) -> list[AttackerEcu]:
    with open(path) as f:
        return [AttackerEcu(d["id"], d["name"], {int(k): v for k, v in d["messages"].items()}, d["target"],skip_attack) for d in json.load(f)]

if __name__ == "__main__":

    # get command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--time",     type=float, default=1.0,  help="Sleep time in seconds")
    parser.add_argument("--skip-attack",     type=int, default=2,  help="Sleep time in seconds")
    parser.add_argument("--debug",    action="store_true",       help="Enable debug mode")
    parser.add_argument("--no-sleep", action="store_true",       help="Set sleep time to 0")
    parser.add_argument("--error-debug", action="store_true",       help="Enable print for error counters and status")
    args = parser.parse_args()

    canSettings.DEBUG = args.debug
    canSettings.ERROR_DEBUG = args.error_debug
    sleep_time = 0 if args.no_sleep else args.time

    # prepare bus and ecus
    ecus = load_ecus(os.path.join("resources","ecus.json"))
    ecus = ecus + load_attacker_ecus(os.path.join("resources","infected_ecus.json"), args.skip_attack)

    canbus = Canbus(sleep_time,ecus)
    canbus.startSimulation()


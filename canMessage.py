from dataclasses import dataclass

@dataclass
class CanMessage:
    """A logical CAN message representation."""
    id: int
    data: bytearray



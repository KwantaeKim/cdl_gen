# -----------------------------------------------------------------------------
# File          : subckt.py
# Author        : Kwantae Kim <kwantae.kim@aalto.fi>
# Group         : TSirc Group, Aalto University
# Created       : 31.May.2025
# -----------------------------------------------------------------------------

class subckt:
    """
    Represents a .SUBCKT (...) .ENDS block in a CDL netlist.
    """
    all_subckts = []

    def __init__(self, name: str, pins: list[str]):
        """
        Parameters
        ----------
        name : str
            The subcircuit name.
        pins : list[str]
            Top-level pin names in the subckt definition.
        """
        self.name = name
        self.pins = pins
        self.devices = []  # list of Device objects
        subckt.all_subckts.append(self)

    def add_device(self, device):
        """Add a Device object to this subcircuit."""
        self.devices.append(device)

    def to_cdl(self) -> str:
        """Convert the subckt definition and its devices into multi-line CDL text."""
        lines = []
        pins_str = " ".join(self.pins)
        lines.append(f".SUBCKT {self.name} {pins_str}")
        for dev in self.devices:
            lines.append(dev.to_cdl())
        lines.append(f".ENDS")
        lines.append("")  # blank line for readability
        return "\n".join(lines)
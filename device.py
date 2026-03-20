# -----------------------------------------------------------------------------
# File          : device.py
# Author        : Kwantae Kim <kwantae.kim@aalto.fi>
# Group         : TSirc Group, Aalto University
# Created       : 31.May.2025
# -----------------------------------------------------------------------------

class device:
    """
    Represents a single SPICE device line in a CDL netlist.
    """

    def __init__(self, name, model, terminals, **params):
        """
        Parameters
        ----------
        name : str
            Instance name.
        model : str
            Model name in the CDL netlist.
        terminals : list[str]
            List of node connections in the order.
        params : dict
            Additional parameters for the device.
        """
        self.name = name
        self.model = model
        self.terminals = terminals
        self.params = params

    def to_cdl(self) -> str:
        """
        Convert this device object into a single line of CDL netlist text.
        """
        # Start with instance name and terminals
        cdl_line = f"{self.name} " + " ".join(self.terminals) + f" {self.model}"

        # Append any parameters in SPICE format: L=..., W=..., etc.
        for key, val in self.params.items():
            cdl_line += f" {key}={val}"

        return cdl_line
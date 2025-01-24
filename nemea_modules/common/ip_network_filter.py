"""
Common ADiCT class to unite the filtering of IP prefixes across different modules.
"""

import re
from typing import Iterable

import pytrap


class IPNetworks:
    """Class for handling IP network filtering with UnirecIPAddrRange."""

    def __init__(self):
        self.networks = set()

    @staticmethod
    def validate_ipv46_network(
        net_str: str, line_no: int = None
    ) -> pytrap.UnirecIPAddrRange:
        try:
            return pytrap.UnirecIPAddrRange(net_str)
        except (ValueError, TypeError, pytrap.TrapError) as e:
            raise ValueError(
                f"Invalid network '{net_str}'"
                + (f" on line {line_no}" if line_no is not None else " passed")
                + f": {e}"
            ) from e

    @classmethod
    def from_file(cls, filepath: str) -> "IPNetworks":
        """Create instance from file containing network strings."""
        instance = cls()
        with open(filepath) as f:
            for line_no, line in enumerate(f, 1):
                net_str = re.sub(r"(#|//).*", "", line).strip()
                if net_str == "":
                    continue
                instance.networks.add(instance.validate_ipv46_network(net_str, line_no))
        return instance

    @classmethod
    def from_list(cls, networks: Iterable[str]) -> "IPNetworks":
        """Create instance from list of network strings."""
        instance = cls()

        for net_str in networks:
            # Validate and add to the set
            instance.networks.add(instance.validate_ipv46_network(net_str))
        return instance

    def __contains__(self, ip: pytrap.UnirecIPAddr) -> bool:
        """Check if IP address belongs to any of the networks."""
        return any(ip in net for net in self.networks)

    def __str__(self) -> str:
        """Return a string representation of the networks."""
        if not self.networks:
            return "No networks configured"
        networks_list = [str(net) for net in self.networks]
        return "\n".join(f"  - {net}" for net in networks_list)

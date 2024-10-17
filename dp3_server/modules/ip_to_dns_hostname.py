"""Secondary module for ADiCT project which translates global IP addresses to DNS hostname (reverse DNS lookup).
"""
import ipaddress
from typing import List

from dns import resolver, reversename
from dns.exception import *

from dp3.common.base_module import BaseModule
from dp3.common.callback_registrar import CallbackRegistrar
from dp3.common.config import PlatformConfig
from dp3.common.task import DataPointTask


class IPtoDNSHostname(BaseModule):
    def __init__(
        self,
        platform_config: PlatformConfig,
        module_config: dict,
        registrar: CallbackRegistrar,
    ):
        super().__init__(platform_config, module_config, registrar)

        self._resolver = resolver.Resolver()
        self._resolver.timeout = module_config.get("timeout", 1)
        self._resolver.lifetime = 3  # Socket is open up to 3 seconds and will perform up to 3 queries in case of 1 second timeout occurence.

        registrar.register_on_entity_creation_hook(self.processing_function, "ip")

    def processing_function(self, eid: str, task: DataPointTask) -> List[DataPointTask]:
        hostname = self.reverse_dns_lookup(eid)

        if not hostname:
            return []

        try:
            # Create new task
            task = DataPointTask(
                etype="ip",
                eid=eid,
                data_points=[
                    {
                        "etype": "ip",
                        "eid": eid,
                        "attr": "hostname",
                        "src": "secondary/ip_to_dns_hostname",
                        "v": hostname,
                    }
                ],
            )

            return [task]
        except Exception as e:
            self.log.error(f"Couldn't create task: {e}")
            return []

    def reverse_dns_lookup(self, ip):
        """
        Return a 'hostname' attribute as a result of DNS PTR query on the IP
        address (key).
        If the hostname cannot be resolved (due to NXDOMAIN, timeout or other
        error), None is returned.
        """
        ip_address = ipaddress.ip_address(ip)
        if ip_address.is_global is True:
            addr = reversename.from_address(ip)
            try:
                answer = self._resolver.query(addr, "PTR")
                result = str(answer.rrset[0])  # get first (it should be only) answer
                if result[-1] == ".":
                    result = result[:-1]  # trim trailing '.'
                return result
            except Timeout as e:
                # timeout for dns lookup
                return None
            except DNSException as e:
                # reverse dns lookup failed
                return None
        else:
            # IP address is private/reserved/etc., so it can't be translated to domain name
            return None

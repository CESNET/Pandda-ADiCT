from typing import List
import dns.exception
from dns import resolver

from dp3.common.base_module import BaseModule
from dp3.common.callback_registrar import CallbackRegistrar
from dp3.common.config import PlatformConfig
from dp3.common.datapoint import DataPointObservationsBase
from dp3.common.task import DataPointTask


class DNSopenResolver(BaseModule):
    def __init__(
        self, platform_config: PlatformConfig, module_config: dict, registrar: CallbackRegistrar
    ):
        super().__init__(platform_config, module_config, registrar)
        self.resolver = resolver.Resolver()
        registrar.register_attr_hook(
            "on_new_observation", self.processing_function, "ip", "open_ports"
        )

    def processing_function(self, eid: str, dp: DataPointObservationsBase) -> List[DataPointTask]:
        if dp.v != 53:
            return []

        self.log.debug(f"IP {eid} has port 53 opened, checking for open resolver...")

        # TODO: don't ask every time a port 53 is reported - add some caching, or store open_resolver attr as
        #  binary (i.e. explicitly store "false" as well) and only try it when the attr is not set yet.
        #  If open_ports type gets changed to int with multi-value, it could maybe be implemented such that
        #  the query would be issued only when 53 is in new_val but not in old_val (i.e. 53 has newly appeared
        #  in the current value of the attribute)
        try:
            is_opened = self.opened_resolver(eid)
        except dns.exception.Timeout as e:
            self.log.warning(
                f"IP {eid}: Didn't receive answer (timeout). Maybe the port 53 is not accessible from everywhere?"
            )
            return []

        if is_opened:
            self.log.debug(f"IP {eid}: Open resolver detected")

            try:
                # Create new task
                task = DataPointTask(
                    etype="ip",
                    eid=eid,
                    data_points=[
                        {
                            "etype": "ip",
                            "eid": eid,
                            "attr": "open_resolver",
                            "src": "secondary/dns_open_resolver",
                            "v": True,
                        }
                    ],
                )

                return [task]
            except Exception as e:
                self.log.error(f"Couldn't create task: {e}")
                return []
        else:
            self.log.debug(f"IP {eid}: Open resolver NOT detected")

        return []

    def opened_resolver(self, eid):
        self.resolver.nameservers = [eid]
        try:
            answer = self.resolver.resolve("test.openresolver.com", "TXT")
        except dns.resolver.NoNameservers:
            return False  # IP refused to resolve the hostname (or another error occurred) - it's not an open resolver
        except dns.resolver.NXDOMAIN:
            return False  # The domain doesn't exist - IP is misconfigured, but not vulnerable as an open resolver
        result = str(answer.rrset[0])
        if result == r'"open-resolver-detected"':
            return True
        return False

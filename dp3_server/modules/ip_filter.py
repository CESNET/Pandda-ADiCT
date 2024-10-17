import ipaddress

from dp3.common.base_module import BaseModule
from dp3.common.callback_registrar import CallbackRegistrar
from dp3.common.config import PlatformConfig
from dp3.common.task import DataPointTask


class IPFilter(BaseModule):
    def __init__(self, config: PlatformConfig, module_config: dict, registrar: CallbackRegistrar):
        super().__init__(config, module_config, registrar)

        registrar.register_allow_entity_creation_hook(self.processing_function, "ip")

    def load_config(self, config: PlatformConfig, module_config: dict) -> None:
        # loading list of prefixes from a file
        self.prefixes = list()
        load_prefixes = module_config.get("prefixes", list())
        for prefix in load_prefixes:
            n = ipaddress.ip_network(prefix)
            network = int(n.network_address)
            mask = int(n.netmask)
            self.prefixes.append([network, mask])

    def processing_function(self, eid: str, _task: DataPointTask) -> bool:
        if not self.prefixes:
            return True  # when prefixes are not specified, all IP addresses pass
        else:
            ip = int(ipaddress.ip_network(eid).network_address)
            for netw, mask in self.prefixes:
                if (ip & mask) == netw:
                    return True
        self.log.debug("{} doesn't match any prefix.".format(eid))
        return False

from typing import List

from dp3.common.base_module import BaseModule
from dp3.common.callback_registrar import CallbackRegistrar
from dp3.common.config import PlatformConfig
from dp3.common.datapoint import DataPointTimeseriesBase
from dp3.common.task import DataPointTask


class IPactivity(BaseModule):
    def __init__(self, platform_config: PlatformConfig, _, registrar: CallbackRegistrar):
        super().__init__(platform_config, {}, registrar)
        registrar.register_on_new_attr_hook(self.processing_function, "ip", "activity")

    def processing_function(self, eid: str, dp: DataPointTimeseriesBase) -> List[DataPointTask]:
        avg_bytes_per_time_step = sum(dp.v.bytes) / len(dp.v.bytes)

        act_class = self.ip_act(avg_bytes_per_time_step)

        try:
            # Create new task
            task = DataPointTask(
                etype="ip",
                eid=eid,
                data_points=[
                    {
                        "etype": "ip",
                        "eid": eid,
                        "attr": "activity_class",
                        "src": "secondary/ip_activity",
                        "v": act_class,
                    }
                ],
            )

            return [task]
        except Exception as e:
            self.log.error(f"Couldn't create task: {e}")
            return []

    def ip_act(self, atr_val):
        if atr_val <= 0:
            act_class = "off"
        elif atr_val < 3750:
            act_class = "idle"
        elif atr_val < 50000:
            act_class = "light"
        elif atr_val < 300000:
            act_class = "medium"
        else:
            act_class = "high"

        return act_class

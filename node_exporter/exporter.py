from .pusher import PrometheusPusher, MetricsName
from returns.maybe import Some, Maybe, Nothing
from .node import Node, Resources
from attrs import define, field
from datetime import timedelta
from typing import List
import attrs
import random
import time


@define
class NodeExporter:
    interval: timedelta
    node_name: str
    gateway_url: str
    _node: Node = field(init=False)
    _pusher: PrometheusPusher = field(init=False)
    _metrics_names: List[str] = field(init=False)

    def __attrs_post_init__(self):
        self._metrics_names = [field.name for field in attrs.fields(Resources)]
        self._node = Node(self.node_name)
        self._pusher = PrometheusPusher(
            self._node.name, self.gateway_url, self._metrics_names
        )

    def _generate_single_metric(self, metric_name: MetricsName):
        max_metric_value: float = getattr(self._node.resources, metric_name)
        match max_metric_value:
            case Some(max_metric_value) if max_metric_value is not Nothing:
                return random.uniform(0, int(max_metric_value))
            case Some(max_metric_value):
                return 0.0
            case Maybe.empty:
                return 0.0

    def generate(self):
        while True:
            generated_values = list(
                map(self._generate_single_metric, self._metrics_names)
            )
            self._pusher.metrics_values = generated_values
            time.sleep(self.interval.total_seconds())

from attrs import define, field
from datetime import timedelta
from pusher import PrometheusPusher, MetricsName
from typing import List
from node import Node
import attrs, random, time


@define
class NodeExporter:
    interval: timedelta
    node_name: str
    gateway_url: str
    _node: Node = field(init=False)
    _pusher: PrometheusPusher = field(init=False)
    _metrics_names: List[str] = field(init=False)

    def __attrs_post_init__(self):
        self._metrics_names = [field.name for field in attrs.fields(Node)]
        self._node = Node(self.node_name)
        self._pusher = PrometheusPusher(
            self._node.name, self.gateway_url, self._metrics_names
        )

    def _generate_single_metric(self, metric_name: MetricsName):
        max_metric_value: float = getattr(metric_name, self._node)
        return random.uniform(0, max_metric_value)

    def generate(self):
        while True:
            generated_values = list(map(self._generate_single_metric, self._metrics_names))
            self._pusher.metrics_values = generated_values
            time.sleep(self.interval.total_seconds())

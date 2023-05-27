from .pusher import PrometheusPusher
from .node import Node, NodeResources
from attrs import define, field
from datetime import timedelta
from typing import List
import attrs, logging


@define
class NodeExporter:
    interval: timedelta
    gateway_url: str
    node: Node
    _pusher: PrometheusPusher = field(init=False)
    _metrics_names: List[str] = field(init=False)

    @property
    def name(self) -> str:
        return self.node.name

    @property
    def node_usage(self) -> Node:
        return self.node.usage

    @node_usage.setter
    def node_usage(self, usage: NodeResources):
        self.node.usage = usage
        self._pusher.metrics_values = self.node.usage

    def __attrs_post_init__(self):
        logging.info("Building Node Exporter")
        self._metrics_names = [
            field.name for field in attrs.fields(self.node.limit.__class__)
        ]
        self._pusher = PrometheusPusher(
            self.node.name, self.gateway_url, self._metrics_names
        )

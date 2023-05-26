from .pusher import PrometheusPusher, MetricsName
from returns.maybe import Some, Maybe, Nothing
from .node import Node, Resources
from attrs import define, field
from datetime import timedelta
from typing import List
import attrs
import random
import time
import logging


@define
class NodeExporter:
    interval: timedelta
    pod_name: str
    pod_namespace: str
    gateway_url: str
    _node: Node = field(init=False)
    _pusher: PrometheusPusher = field(init=False)
    _metrics_names: List[str] = field(init=False)

    def __attrs_post_init__(self):
        logging.info("Building Node Exporter")
        self._metrics_names = [field.name for field in attrs.fields(Resources)]
        self._node = Node(self.pod_name, self.pod_namespace)
        self._pusher = PrometheusPusher(
            self._node.name, self.gateway_url, self._metrics_names
        )

    def _generate_single_metric(self, metric_name: MetricsName):
        max_metric_value: float = getattr(self._node.resources, metric_name)
        match max_metric_value:
            case Some(max_metric_value) if max_metric_value is not Nothing:
                resource_usage = random.uniform(0, int(max_metric_value))
                logging.debug(f"Pushing into prometheus: ({metric_name},{resource_usage})")
                return resource_usage
            case Some(max_metric_value):
                resource_usage = 0.0
                logging.debug(f"Pushing into prometheus: ({metric_name},{resource_usage})")
                return resource_usage
            case Maybe.empty:
                resource_usage = 0.0
                logging.debug(f"Pushing into prometheus: ({metric_name},{resource_usage})")
                return resource_usage

    def generate(self):
        sleep_seconds: int = self.interval.total_seconds()
        while True:
            generated_values = list(
                map(self._generate_single_metric, self._metrics_names)
            )
            logging.info("Pushing Metrics into proemtheus")
            self._pusher.metrics_values = generated_values
            logging.info(f"Sleeping: {sleep_seconds} seconds")
            time.sleep(sleep_seconds)

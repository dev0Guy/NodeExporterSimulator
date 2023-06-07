from prometheus_client.registry import CollectorRegistry
from prometheus_client import Gauge, push_to_gateway
from attrs import define, Factory, field
from typing import Dict, List, Tuple

# Type Alias
MetricsName = str
MetricsValue = float


@define
class PrometheusPusher:
    job_name: str
    gateway_url: str
    metrics_names: List[MetricsName]
    _current_metric_value: List[MetricsValue] = field(init=False)
    _metric_collector_mapper: Dict[MetricsName, Gauge] = field(init=False)
    _registry: CollectorRegistry = Factory(CollectorRegistry)

    def __attrs_post_init__(self):
        self._metric_collector_mapper = {
            metric: Gauge(metric, f"{metric} Usage (%)", registry=self._registry)
            for metric in self.metrics_names
        }
        self._current_metric_value = [0] * len(self.metrics_names)

    def _push_metrics(self):
        metric_gauge_and_value: List[Tuple[Gauge, MetricsValue]] = zip(
            self._metric_collector_mapper.values(), self._current_metric_value
        )
        for metric_gauge, metric_val in metric_gauge_and_value:
            metric_gauge.set(metric_val)
        push_to_gateway(
            gateway=self.gateway_url, job=self.job_name, registry=self._registry
        )

    @property
    def metrics_values(self) -> List[MetricsValue]:
        return self._current_metric_value

    @metrics_values.setter
    def metrics_values(self, values: List[MetricsValue]):
        if len(values) != len(self._current_metric_value):
            raise ValueError(
                f"Metrics values can only be set with a list with the same length. expexted {len(self._current_metric_value)} and got {len(values)}"
            )
        self._current_metric_value = values
        self._push_metrics()

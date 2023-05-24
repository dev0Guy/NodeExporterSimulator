from returns.maybe import Maybe, Nothing, Some
from attrs import define, field, Factory
from kubernetes import client, config


@define
class Resources:
    net_bandwidth: Maybe[str] = field(default=Nothing)
    memory: Maybe[str] = field(default=Nothing)
    cpu: Maybe[int] = field(default=Nothing)
    gpu: Maybe[str] = field(default=Nothing)

    def __attrs_post_init__(self):
        match self.memory:
            case Some(memory):
                self.memory = Some(memory[:-2])
            case Maybe.empty:
                pass


@define
class Node:
    name: str
    resources: Resources = Factory(Resources)

    @classmethod
    def fetch_node_resource(cls, node_name: str) -> Resources:
        api_client = client.CoreV1Api()
        node = api_client.read_node(node_name)

        # Fetch all node resources
        capacity: dict = node.status.capacity

        cpu_capacity = Maybe.from_optional(capacity.get("cpu", Nothing))

        memory_capacity = Maybe.from_optional(capacity.get("memory", Nothing))

        network_bandwidth_capacity = Maybe.from_optional(
            capacity.get("network_bandwidth", Nothing)
        )

        gpu_capacity = Maybe.from_optional(capacity.get("nvidia.com/gpu", Nothing))

        return Resources(
            cpu=cpu_capacity,
            gpu=gpu_capacity,
            memory=memory_capacity,
            net_bandwidth=network_bandwidth_capacity,
        )

    def __attrs_post_init__(self):
        config.load_incluster_config()
        self.resources = self.fetch_node_resource(self.name)

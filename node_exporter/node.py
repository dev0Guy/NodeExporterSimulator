from returns.maybe import Maybe, Nothing, Some
from returns.result import Success, Failure
from returns.result import safe
from attrs import define, field, Factory
from kubernetes import client, config
from typing import Tuple
import logging


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
                logging.info(f"Build Resource Object")
            case Maybe.empty:
                pass


@define
class Node:
    name: str = field(init=False)
    _pod_name: str
    _pod_namespace: str
    resources: Resources = Factory(Resources)

    @classmethod
    @safe(exceptions=(AttributeError))
    def fetch_node_resource(cls, pod_name: str, pod_namespace: str) -> Tuple[str, Resources]:
        api_client = client.CoreV1Api()
        logging.debug(f"Called fetch_node_resource with arguments of {pod_name} , {pod_namespace}")
        pod = api_client.read_namespaced_pod(pod_name, pod_namespace)
        node_name = pod.spec.node_name
        logging.info(f"Load Node {node_name} Resources")
        node = api_client.read_node(node_name)

        # Fetch all node resources
        capacity: dict = node.status.capacity

        cpu_capacity = Maybe.from_optional(capacity.get("cpu", Nothing))

        memory_capacity = Maybe.from_optional(capacity.get("memory", Nothing))

        network_bandwidth_capacity = Maybe.from_optional(
            capacity.get("network_bandwidth", Nothing)
        )

        gpu_capacity = Maybe.from_optional(capacity.get("nvidia.com/gpu", Nothing))
        
        return (node_name, Resources(
            cpu=cpu_capacity,
            gpu=gpu_capacity,
            memory=memory_capacity,
            net_bandwidth=network_bandwidth_capacity,
        ))

    def __attrs_post_init__(self):
        # if cannt load config file
        match config.load_incluster_config():
            case Failure(config.config_exception.ConfigException as exp):
                raise exp
        match self.fetch_node_resource(self._pod_name, self._pod_namespace):
            case Success(resources):
                self.name, resources = resources
                logging.debug(f"Build Node {self.name}: {resources}")
                self.resources = resources
            case Failure(AttributeError as exp):
                raise exp

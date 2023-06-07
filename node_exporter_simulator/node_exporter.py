from .prometheus_pusher import PrometheusPusher
from kubernetes import client, config
from .node import NodeResources, Node
from datetime import timedelta
from functools import reduce
from typing import List, Tuple
import asyncio
import logging
import socket
import attrs
import re
import uvloop
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
import kopf

@attrs.define
class NodeExporter:
    url: str
    interval: timedelta
    namespace: str
    _pusher: PrometheusPusher = attrs.field(init=False)
    _metrics_names: List[str] = attrs.field(init=False)
    _running_pods: dict = attrs.Factory(dict)
    _node: Node = attrs.field(init=False)
    _lock: asyncio.Lock = attrs.Factory(asyncio.Lock)

    @classmethod
    def __load_config(self, **kwargs):
        # config.load_kube_config()
        config.load_incluster_config()

    @classmethod
    def __create_node(cls, pod_namespace) -> Node:
        api: client.CoreV1Api = client.CoreV1Api()
        pod_name = socket.gethostname()
        logging.debug(
            f"Called fetch_node_resource with arguments of {pod_name} , {pod_namespace}"
        )
        pod = api.read_namespaced_pod(pod_name, pod_namespace)
        node_name = pod.spec.node_name
        logging.info(f"Load Node {node_name} NodeResources")
        node = api.read_node(node_name)
        node_resource = NodeResources()
        node_fields: str = list(
            map(lambda x: x.name, attrs.fields(node_resource.__class__))
        )
        allocate = node.status.allocatable
        for resource_name in allocate.keys():
            if resource_name in node_fields:
                logging.info(
                    f"Container get limit in {resource_name} and setting it in {type(node_resource)}"
                )
                node_resource.__setattr__(resource_name, allocate.get(resource_name))
            else:
                logging.warning(
                    f"Container have a limit of {resource_name} which does not exist in Node"
                )
        logging.info(f"FINISH creating Node {node_name}")
        return Node(node_name, node_resource)

    @classmethod
    def __object_attr_values(cls, _obj: object) -> List[Tuple[str,float]]:
        return list(
            map(
                lambda x: _obj.__getattribute__(x).value, 
                map(
                    lambda x: x.name,
                    attrs.fields(_obj.__class__)
                )
            )
        )    

    @classmethod
    def __in__node(cls, node: Node, spec: dict):
        return node.name == spec.get('nodeName')

    def __attrs_post_init__(self):
        self.__load_config()
        # dsadsa
        self._node = self.__create_node(self.namespace)
        # Get all resource to reocrd using NodeStruct
        self._metrics_names = [
            field.name for field in attrs.fields(self._node.limit.__class__)
        ]
        # create prometheus pusher
        self._pusher = PrometheusPusher(self._node.name, self.url, self._metrics_names)
        # add kopf func
        kopf.on.startup()(self.__startup_tasks)
        kopf.on.delete("v1", "pods")(self.__watch_pod_deletion)
        kopf.on.create("v1", "pods")(self.__watch_pods_createion)
        kopf.on.update("v1", "pods")(self.__watch_pods_createion)
        logging.warning("FINISH BUILDING OBJECT")

    async def __watch_pods_createion(
        self,  spec, name, namespace, uid, **kwargs
    ):
        if self.__in__node(self._node, spec):
            logging.info(
                f"Pod {name} Has been Created/Updated in Namespace {namespace}"
            )
            node_resources = list(
                map(
                    lambda x: x.name,
                    attrs.fields(self._node.limit.__class__),
                )
            )
            pod_resource = NodeResources()
            for container in spec.get("containers", {}):
                limits: dict = container.get("resources", {}).get("limits", None)
                container_name = container.get("name", "UNKNOWN")
                if limits is None:
                    logging.warning(
                        f"Pod {name} has container {container_name} with no limit"
                    )
                    continue
                for resource_name, resource_val in limits.items():
                    if resource_name in node_resources:
                        val = resource_val
                        match resource_val:
                            case int(resource_val):
                                val = float(resource_val)
                            case float(resource_val):
                                val = resource_val
                            case str(resource_val):
                                val = "".join(re.findall(r"\d+", resource_val))
                                val = float(val)
                            case _:
                                logging.warning(
                                    f"Pod {name} has container {container_name} with un reconize limit {resource_val} "
                                )
                                continue
                        new_resource_val = (
                            pod_resource.__getattribute__(resource_name) + val
                        )
                        pod_resource.__setattr__(resource_name, new_resource_val)
                    else:
                        logging.warning(
                            f"Container in pod: {name} Have limit of {resource_name} witch doen't exist in {self._node.limit.__class__} "
                        )
                async with self._lock:
                    self._running_pods[uid] = pod_resource

    async def __watch_pod_deletion(self, name, namespace, spec, uid, **kwargs):
        if self.__in__node(self._node, spec):
            logging.info(
                f"Pod {name} Has been Created/Updated in Namespace {namespace}"
            )
            async with self._lock:
                if uid in self._running_pods:
                    self._running_pods.pop(uid)

    async def __start(self, **kwargs):
        logging.info("Starting Node Exporter Simulator")
        logging.info(f"Prometheus gateway url: {self.url}")
        sleep_seconds: int = self.interval.total_seconds()
        logging.info(f"Sleeping time set as {sleep_seconds}s")
        logging.info(f"Start Pushin Metrics into prometheus")
        while True:
            async with self._lock:
                pods_resources = [*self._running_pods.values()]
            node_resources = (
                NodeResources()
                if len(pods_resources) <= 0
                else reduce(lambda a, b: a + b, pods_resources)
            )
            logging.debug(f"Collect Node Metrics. Got Max {node_resources}")
            node_usage: NodeResources = node_resources.random_generate()
            usage_as_list = self.__object_attr_values(node_usage)
            logging.warning(f"Collect Node Metrics. Gnerated {node_resources}")
            self._pusher.metrics_values = self._node.usage = usage_as_list
            await asyncio.sleep(sleep_seconds)

    async def __startup_tasks(self, **kwargs):
        # Start the async task in the background
        asyncio.create_task(self.__start(**kwargs))

    def run(self):
        kopf.run()
 
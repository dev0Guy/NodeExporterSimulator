from node_exporter import NodeExporter
from node_exporter.node import Node, Resources
from kubernetes import client, config
from datetime import timedelta
from typing import List
from functools import reduce
import logging, kopf, socket, time
import os, regex_spm, attrs, re
import asyncio

config.load_incluster_config()

@kopf.on.update("v1", "pods")
@kopf.on.create("v1", "pods")
def pod_creation(spec, name, namespace, uid, **kwargs):
    logging.warn(f"Event: {'event_type'} Pod: {name} Namespace: {namespace}")
    node_resources =  list(map(lambda x: x.name ,attrs.fields(KubernetesMannager.NODE_EXPORTER.node.limit.__class__)))
    pod_resource = Resources()
    for container in spec.get("containers",{}):
        limits: dict = container.get("resources",{}).get("limits")
        if limits is None:
            logging.error("limit is not spec")
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
                        val = ''.join(re.findall(r'\d+', resource_val))
                        val = float(val)
                    case _:
                        logging.error("FL<D<sl;fl,sd")
                        continue
                new_resource_val = pod_resource.__getattribute__(resource_name) + val
                pod_resource.__setattr__(resource_name, new_resource_val)
            else:
                logging.warn(f"Container in pod: {name} Have limit of {resource_name} witch doen't exist in {KubernetesMannager.NODE_EXPORTER.node.limit.__class__} ")
    KubernetesMannager.PODS[uid] = pod_resource
    logging.warn(f"Added Pod{uid} informatin")

@kopf.on.delete("v1", "pods")
def pod_deletion( name, namespace, uid, **kwargs):
    logging.warn(f"Event: {'event_type'} Pod: {name} Namespace: {namespace}")
    if uid in KubernetesMannager.PODS:
        KubernetesMannager.PODS.pop(uid)

def load_prometheus_push_interval() -> int:
    interval_str = os.environ["PUSH_INTERVAL"]
    logging.info(f"Parsing PUSH_INTERVAL enviorment varibale {interval_str}")
    match regex_spm.fullmatch_in(interval_str):
        case r"^(?P<time>\d+)([s])$" as input:  # seconds
            logging.debug(f"Loaded prometheus interval as seconds. {input}")
            return timedelta(seconds=int(input["time"]))
        case r"^(?P<time>\d+)([m])$" as input:  # minutes
            logging.debug(f"Loaded prometheus interval as minutes. {input}")
            return timedelta(minutes=int(input["time"]))
        case r"^(?P<time>\d+)([h])$" as input:  # hours
            logging.debug(f"Loaded prometheus interval as hours. {input}")
            return timedelta(hours=int(input["time"]))
        case _:
            raise ValueError(f"Time Foramt is not supported. {interval_str}")

def create_node() -> Node:
    api = client.CoreV1Api()
    pod_namespace = os.environ.get("POD_NAMESPACE")
    pod_name = 'node-exporter-simulator-df2wh' #socket.gethostname()
    logging.debug(
        f"Called fetch_node_resource with arguments of {pod_name} , {pod_namespace}"
    )
    pod = api.read_namespaced_pod(pod_name, pod_namespace)
    node_name = pod.spec.node_name
    logging.info(f"Load Node {node_name} Resources")
    node = api.read_node(node_name)
    node_resource = Resources()
    node_fields: str = list(map(lambda x: x.name, attrs.fields(node_resource.__class__)))
    allocate = node.status.allocatable
    for resource_name in allocate.keys():
        if resource_name in node_fields:
            logging.info(f"Container get limit in {resource_name} and setting it in {type(node_resource)}")
            node_resource.__setattr__(
                resource_name, allocate.get(resource_name)
            )
        else:
            logging.warn(
                f"Container have a limit of {resource_name} which does not exist in Node"
            )
    logging.info(f"FINISH creating Node {node_name}")
    return Node(node_name, node_resource)

class KubernetesMannager:
    INTERVAL: timedelta = load_prometheus_push_interval()
    GATEWAY_URL: str = os.environ["PROMETHEUS_GATEWAY_URL"]
    NODE_EXPORTER: NodeExporter = NodeExporter(INTERVAL, GATEWAY_URL, create_node())
    PODS: dict = {}

    @staticmethod
    async def start():
        sleep_seconds: int = KubernetesMannager.INTERVAL.total_seconds()
        while True:
            logging.info("Pushing Metrics into proemtheus")
            pods_resources = [*KubernetesMannager.PODS.values()]
            max_node_usage = Resources() if len(pods_resources) <= 0 else reduce(lambda a,b: a + b, pods_resources)
            usage_as_list = list(attrs.asdict(max_node_usage).values())
            KubernetesMannager.NODE_EXPORTER.node_usage = usage_as_list
            logging.warn(f"Sleeping: {sleep_seconds} seconds")
            await asyncio.sleep(sleep_seconds)


async def main():
    task1 = asyncio.create_task(kopf.operator())
    task2 = asyncio.create_task(KubernetesMannager.start())
    await asyncio.gather(task1, task2)

if __name__ == "__main__":  
    asyncio.run(main())
    
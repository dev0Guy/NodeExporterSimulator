from returns.maybe import Maybe, Nothing, Some
from returns.result import Result, Success, Failure, safe
from node_exporter import NodeExporter
from datetime import timedelta
import os, regex_spm, logging
import socket


logging.basicConfig(level=logging.INFO)


def load_pod_namespace() -> str:
    return os.environ.get("POD_NAMESPACE")

def load_pod_name() -> str:
    return socket.gethostname()

def load_prometheus_gateway_url() -> str:
    return os.environ["PROMETHEUS_GATEWAY_URL"]

@safe(exceptions=ValueError)
def load_prometheus_push_interval() -> int:
    interval_str = os.environ["PUSH_INTERVAL"]
    logging.info(f"Parsing PUSH_INTERVAL enviorment varibale {interval_str}")
    match regex_spm.fullmatch_in(interval_str):
        case r"^(?P<time>\d+)([s])$" as input: # seconds
            logging.debug(f"Loaded prometheus interval as seconds. {input}")
            return timedelta(seconds=int(input['time']))
        case r"^(?P<time>\d+)([m])$" as input: # minutes
            logging.debug(f"Loaded prometheus interval as minutes. {input}")
            return timedelta(minutes=int(input['time']))
        case r"^(?P<time>\d+)([h])$" as input: # hours
            logging.debug(f"Loaded prometheus interval as hours. {input}")
            return timedelta(hours=int(input['time']))
        case _:
            raise ValueError(f"Time Foramt is not supported. {interval_str}")


if __name__ == "__main__":
    pod_name_space = load_pod_namespace()
    logging.info(f'Loaded Env Varibale "POD_NAMESPACE: {pod_name_space}"')
    pod_name = load_pod_name()
    logging.info(f'Loaded HostName: {pod_name}')
    gateway_url = load_prometheus_gateway_url()
    logging.info(f'Loaded Env Varibale "PROMETHEUS_GATEWAY_URL": {gateway_url}')
    match load_prometheus_push_interval():
        case Success(interval):
            NodeExporter(interval, pod_name, pod_name_space, gateway_url).generate()
        case Failure(ValueError as e ):
            logging.error(str(e))
        case Failure(Exception as e):
            raise e
from returns.maybe import Maybe, Nothing, Some
from returns.result import Result, Success, Failure, safe
from node_exporter import NodeExporter
from datetime import timedelta
import os, regex_spm, logging

logging.basicConfig(level=logging.INFO)


def load_node_name() -> str:
    return os.environ["MY_NODE_NAME"]

def load_prometheus_gateway_url() -> str:
    return os.environ["PROMETHEUS_GATEWAY_URL"]

@safe(exceptions=ValueError)
def load_prometheus_push_interval() -> int:
    interval_str = os.environ["PUSH_INTERVAL"]
    logging.info("Parsing PUSH_INTERVAL enviorment varibale")
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
    node_name = load_node_name()
    gateway_url = load_prometheus_gateway_url()
    logging.info('Loaded Env Varibale "MY_NODE_NAME"')
    logging.info('Loaded Env Varibale "PROMETHEUS_GATEWAY_URL"')
    match load_prometheus_push_interval():
        case Success(interval):
            NodeExporter(interval, node_name, gateway_url).generate()
        case Failure(ValueError as e ):
            logging.error(str(e))
        case Failure(Exception as e):
            raise e
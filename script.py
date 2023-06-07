from node_exporter_simulator import NodeExporter
from datetime import timedelta
import regex_spm
import logging
import os

def load_prometheus_push_interval() -> int:
    interval_str = os.environ["PUSH_INTERVAL"]
    logging.warning(f"Parsing PUSH_INTERVAL enviorment varibale {interval_str}")
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


if __name__ == "__main__":
    NodeExporter(
        os.environ["PROMETHEUS_GATEWAY_URL"],
        load_prometheus_push_interval(),
        os.environ["POD_NAMESPACE"]
    ).run()

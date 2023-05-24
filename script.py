from returns.maybe import Maybe, Nothing, Some
from node_exporter import NodeExporter
from datetime import timedelta
import os, regex_spm

local_node_name: Maybe[str] = Maybe.from_optional(
    os.environ.get("MY_NODE_NAME", Nothing)
)

prometheus_gateway_url: Maybe[str] = Maybe.from_optional(
    os.environ.get("PROMETHEUS_GATEWAY_URL", Nothing)
)

prometheus_push_interval: Maybe[str] = Maybe.from_optional(
    os.environ.get("PUSH_INTERVAL", Nothing)
)

class TimeInput:
    seconds = r"^(?P<time>\d+)([s])$" 
    minutes = r"^(?P<time>\d+)([m])$" 
    hours = r"^(?P<time>\d+)([h])$" 

    @classmethod
    def convert(cls, input: str) -> timedelta:
        match regex_spm.fullmatch_in(input):
            case TimeInput.seconds as input:
                return timedelta(seconds=int(input['time']))
            case TimeInput.minutes as input:
                return timedelta(minutes=int(input['time']))
            case TimeInput.hours as input:
                return timedelta(hours=int(input['time']))
            case _:
                raise ValueError(f"")


if __name__ == "__main__":
    if local_node_name is Nothing:
        raise ValueError("MY_NODE_NAME enviorment varibale is missing")
    if prometheus_gateway_url is Nothing:
        raise ValueError("PROMETHEUS_GATEWAY_URL enviorment varibale is missing")
    # get original values: 
    local_node_name = local_node_name.value_or('NoVal')
    prometheus_gateway_url = prometheus_gateway_url.value_or('NoVal')


    match prometheus_push_interval:
        case Some(prometheus_push_interval):
            time_interval: timedelta = TimeInput.convert(prometheus_push_interval)
            NodeExporter(time_interval,local_node_name,prometheus_gateway_url).generate()
        case Maybe.empty:
            raise ValueError("PROMETHEUS_GATEWAY_URL enviorment varibale is missing")

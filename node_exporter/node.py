from returns.maybe import Maybe, Nothing, Some
from returns.result import Success, Failure
from returns.result import safe
from attrs import define, field, Factory
from kubernetes import client, config
from typing import Tuple
import logging, kopf
import itertools, attrs


@define
class Resources:
    net_bandwidth: float = field(default=0.0)
    memory: float = field(default=0.0)
    cpu: float = field(default=0.0)
    gpu: float = field(default=0.0)

    def __add__(self, other):
        if self.__class__ is other.__class__:
            raise ValueError(f"Only Resources Type can be added. not {type(other)}")
        new_resource = self.__class__()
        for _field in attrs.fields(self.__class__):
            combined_val: float = self.__getattribute__(
                _field.name
            ) + other.__getattribute__(_field.name)
            new_resource.__setattr__(_field.name, combined_val)
        return new_resource


@define
class Node:
    name: str
    limit: Resources
    _usage: Resources = Factory(Resources)

    @property
    def usage(self) -> Resources:
        return self._usage

    @usage.setter
    def usage(self, usage: Resources):
        logging.debug(f"Updateing usage_property: {usage}")
        self._usage = usage

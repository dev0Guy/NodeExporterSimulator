from .resouce import Resource
from attrs import define, Factory
import attrs


@define
class NodeResources:
    net_bandwidth: Resource = Factory(Resource)
    memory: Resource = Factory(Resource)
    cpu: Resource = Factory(Resource.create_district)
    gpu: Resource = Factory(Resource.create_district)

    def __add__(self, other):
        if self.__class__ is other.__class__:
            raise ValueError(
                f"Only {self.__class__} Type can be added. not {other.__class__:}"
            )
        new_resource = self.__class__()
        for _field in attrs.fields(self.__class__):
            combined_val: float = self.__getattribute__(
                _field.name
            ) + other.__getattribute__(_field.name)
            new_resource.__setattr__(_field.name, combined_val)
        return new_resource

    def random_generate(self) -> "NodeResources":
        tmp: NodeResources = self.__class__()
        for _field in attrs.fields(self.__class__):
            resource: Resource = self.__getattribute__(_field.name).random()
            tmp.__setattr__(_field.name, resource)
        return tmp


@define
class Node:
    name: str
    limit: NodeResources
    _usage: NodeResources = Factory(NodeResources)

    @property
    def usage(self) -> NodeResources:
        return self._usage

    @usage.setter
    def usage(self, usage: NodeResources):
        self._usage = usage

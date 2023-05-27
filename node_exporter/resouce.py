from attrs import define, field
from enum import Enum
import random


class ResourceType(Enum):
    DISCRETE = 0
    NUMERICAL = 1


@define
class Resource:
    kind: ResourceType = field(default=ResourceType.NUMERICAL)
    _value: float = field(default=0.0)

    @property
    def value(self) -> float:
        return self._value

    @classmethod
    def create_district(cls) -> "Resource":
        return cls(ResourceType.DISCRETE, 0.0)

    def __str__(self) -> str:
        return str(self._value)

    def __repr__(self) -> str:
        return str(self._value)

    def __eq__(self, __value: object) -> bool:
        match __value:
            case self.__class__(tmp):
                return self._value == tmp._value
            case float(tmp):
                return self._value == tmp
            case _:
                return False

    def __add__(self, __value: object) -> "Resource":
        match (__value):
            case self.__class__(tmp):
                return self.__class__(
                    max(self.kind, tmp.kind), self._value + tmp._value_
                )
            case float(tmp):
                return self.__class__(ResourceType.NUMERICAL, self._value + tmp)
            case _:
                raise TypeError(
                    f"{self.__class__} Can only be added with Float or {self.__class__}. Got {__value.__class__}"
                )

    def __sub__(self, __value: object) -> "Resource":
        # TODO: add exception for negative numbers
        match (__value):
            case self.__class__(tmp):
                return self.__class__(
                    max(self.kind, tmp.kind), abs(self._value - tmp._value_)
                )
            case float(tmp):
                return self.__class__(ResourceType.NUMERICAL, abs(self._value - tmp))
            case _:
                raise TypeError(
                    f"{self.__class__} Can only be added with Float or {self.__class__}. Got {__value.__class__}"
                )

    def random(self) -> "Resource":
        match self.kind:
            case ResourceType.DISCRETE:
                return self.__class__(
                    ResourceType.DISCRETE, random.randint(0.0, self._value)
                )
            case ResourceType.NUMERICAL:
                return self.__class__(
                    ResourceType.NUMERICAL, random.uniform(0.0, self._value)
                )
            case _:
                TypeError(
                    f"{self.__class__} kind could only be of type {'ResourceType'}. Got {self.kind.__class__}"
                )

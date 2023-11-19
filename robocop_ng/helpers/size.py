from enum import IntEnum, auto
from typing import Self


class Size(IntEnum):
    KB = auto()
    KiB = auto()
    MB = auto()
    MiB = auto()
    GB = auto()
    GiB = auto()

    @classmethod
    def names(cls) -> list[str]:
        return [size.name for size in cls]

    @classmethod
    def from_name(cls, name: str) -> Self:
        for size in cls:
            if size.name.lower() == name.lower():
                return size
        raise ValueError(f"No matching member found for: {name}")

    @property
    def _is_si_unit(self) -> bool:
        return self.value % 2 != 0

    @property
    def _unit_value(self) -> int:
        return self.value // 2 + (1 if self._is_si_unit else 0)

    @property
    def _base_factor(self) -> int:
        return 10**3 if self._is_si_unit else 2**10

    @property
    def _byte_factor(self) -> int:
        return (
            10 ** (3 * self._unit_value)
            if self._is_si_unit
            else 2 ** (10 * self._unit_value)
        )

    def convert(self, value: float, fmt: Self) -> float:
        if self == fmt:
            return value
        if self._is_si_unit == fmt._is_si_unit:
            if self < fmt:
                return value / self._base_factor ** (fmt._unit_value - self._unit_value)
            else:
                return value * self._base_factor ** (self._unit_value - fmt._unit_value)
        else:
            return value * (self._byte_factor / fmt._byte_factor)

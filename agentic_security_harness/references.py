"""Typed references to datasets and installed attack extensions."""

from dataclasses import dataclass, field
from importlib import import_module


@dataclass(frozen=True)
class Source:
    kind: str
    name: str
    options: dict = field(default_factory=dict)
    limit: int = 100

    def __post_init__(self):
        if self.kind not in {"dataset", "csv", "module"}:
            raise ValueError("Source kind must be dataset, csv, or module")
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("Source name must be nonempty")
        if type(self.limit) is not int or self.limit < 1:
            raise ValueError("Source limit must be a positive integer")
        if not isinstance(self.options, dict):
            raise ValueError("Source options must be an object")


@dataclass(frozen=True)
class Technique:
    kind: str
    name: str
    options: dict = field(default_factory=dict)

    def __post_init__(self):
        if self.kind not in {"builtin", "module"}:
            raise ValueError("Technique kind must be builtin or module")
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("Technique name must be nonempty")
        if not isinstance(self.options, dict):
            raise ValueError("Technique options must be an object")


def resolve_callable(name):
    module, separator, attribute = name.partition(":")
    if not separator or not module or not attribute.isidentifier():
        raise ValueError("Module reference must be installed.package:callable")
    fn = getattr(import_module(module), attribute)
    if not callable(fn):
        raise ValueError(f"Module reference is not callable: {name}")
    return fn

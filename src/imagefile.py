from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict


@dataclass
class ImageFile:
    id: str
    path: Path
    status: str
    properties: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            '__type__': 'ImageFile',
            'id': self.id,
            'path': self.path.as_posix(),
            'properties': self.properties,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'ImageFile':
        props = dict(d.get('properties', {}))

        # Backward-compat if older JSON had flattened extra keys
        for k, v in d.items():
            if k not in ('__type__', 'id', 'path', 'properties'):
                props[k] = v

        return cls(
            id=d['id'],
            path=Path(d['path']),
            properties=props,
        )

    def __getattr__(self, name: str):
        alt = '_' + name

        if name in self.properties:
            v = self.properties[name]
            if v is None and alt in self.properties:
                return self.properties[alt]
            return v

        if alt in self.properties:
            return self.properties[alt]

        raise AttributeError(f"{type(self).__name__} has no attribute '{name}'")

    def __setattr__(self, name, value):
        if name in ('id', 'path', 'status', 'properties') or name in getattr(self, '__dataclass_fields__', {}):
            object.__setattr__(self, name, value)
            return
        self.properties[name] = value

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
            'status': self.status,
            'properties': self.properties,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'ImageFile':
        props = dict(d.get('properties', {}))

        # Backward-compat if older JSON had flattened extra keys
        for k, v in d.items():
            if k not in ('__type__', 'id', 'path', 'properties', 'status'):
                props[k] = v

        return cls(
            id=d['id'],
            path=Path(d['path']),
            status=d['status'],
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

        return None

    def __getitem__(self, key: str) -> Any:
        return self.__getattr__(key)

    def __setattr__(self, name, value):
        if name in ('id', 'path', 'status', 'properties') or name in getattr(self, '__dataclass_fields__', {}):
            object.__setattr__(self, name, value)
            return
        self.properties[name] = value

    def __setitem__(self, key: str, value: Any) -> None:
        self.__setattr__(name=key, value=value)

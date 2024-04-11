from dataclasses import dataclass
from enum import Enum, auto
from typing import (
    Sequence,
    Optional,
    FrozenSet,
    Any,
    Mapping,
)
from pathlib import Path
from proj.dtgen.render_utils import (
    IncludeSpec,
)

try:
    import tomllib as toml
except ImportError:
    import toml

class Feature(Enum):
    JSON = auto()
    EQ = auto()
    ORD = auto()
    HASH = auto()
    FMT = auto()
    RAPIDCHECK = auto()

@dataclass(frozen=True)
class IterSpec:
    field: str

@dataclass(frozen=True)
class FieldSpec:
    name: str
    type_: str
    delegate_iter: bool
    _json_key: Optional[str]

    @property
    def json_key(self) -> str:
        if self._json_key is None:
            return self.name
        else:
            return self._json_key

@dataclass(frozen=True)
class StructSpec:
    includes: Sequence[IncludeSpec]
    namespace: Optional[str]
    template_params: Sequence[str]
    name: str
    fields: Sequence[FieldSpec]
    features: FrozenSet[Feature]

    @property
    def fields_by_name(self) -> Mapping[str, FieldSpec]:
        return {field.name : field for field in self.fields}

    @property
    def delegate_iter(self) -> Optional[IterSpec]:
        delegates = [field for field in self.fields if field.delegate_iter is True]
        if len(delegates) == 0:
            return None
        elif len(delegates) == 1:
            return IterSpec(field=delegates[0].name)
        else:
            raise ValueError('Found multiple delegate fields')

def parse_feature(raw: str) -> Feature:
    if raw == 'json':
        return Feature.JSON
    elif raw == 'eq':
        return Feature.EQ
    elif raw == 'ord':
        return Feature.ORD
    elif raw == 'hash':
        return Feature.HASH
    elif raw == 'rapidcheck':
        return Feature.RAPIDCHECK
    elif raw == 'fmt':
        return Feature.FMT
    else:
        raise ValueError(f'Unknown feature: {raw}')

def parse_field_spec(raw: Mapping[str, Any]) -> FieldSpec:
    return FieldSpec(
        name=raw['name'],
        type_=raw['type'],
        delegate_iter=raw.get('delegate_iter', False),
        _json_key=raw.get('json_key'),
    )

def parse_include_spec(raw: str) -> IncludeSpec:
    if raw.startswith('<') and raw.endswith('>'):
        return IncludeSpec(path=raw[1:-1], system=True)
    else:
        return IncludeSpec(path=raw, system=False)

def parse_struct_spec(raw: Mapping[str, Any]) -> StructSpec:
    return StructSpec(
        namespace=raw.get('namespace', None),
        includes=[parse_include_spec(include) for include in raw.get('includes', [])],
        template_params=raw.get('template_params', ()),
        name=raw['name'],
        fields=[parse_field_spec(field) for field in raw['fields']],
        features=frozenset([parse_feature(feature) for feature in raw['features']]),
        delegate_iter=raw.get('delegate_iter', None),
    )

def load_spec(path: Path) -> StructSpec:
    try:
        with path.open('r') as f:
            raw = toml.loads(f.read())
    except toml.TOMLDecodeError as e:
        raise RuntimeError(f'Failed to load spec {path}') from e
    try:
        return parse_struct_spec(raw)
    except KeyError as e:
        raise RuntimeError(f'Failed to parse spec {path}') from e
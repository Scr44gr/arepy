from __future__ import annotations

from collections import OrderedDict
from typing import (Any, Callable, Generic, Mapping, Sequence, Type, TypeVar,
                    TypeVarTuple)

import numpy as np
from numpy.typing import NDArray

from arepy.ecs.components import Component
from arepy.ecs.entities import Entity
from arepy.ecs.registry import Registry
from arepy.ecs.utils import Signature

TEntity = TypeVar("TEntity")
TFilter = TypeVar("TFilter")
TBatchComponents = TypeVarTuple("TBatchComponents")
FloatBatch = NDArray[np.float64]
ScalarBatch = NDArray[Any]
BoolMask = NDArray[np.bool_]


class With(Generic[*TBatchComponents]): ...


class Without(Generic[*TBatchComponents]): ...


class Vec2Batch:
    x: FloatBatch
    y: FloatBatch

    def __init__(self, x: FloatBatch, y: FloatBatch) -> None: ...
    def __len__(self) -> int: ...


class Vec3Batch:
    x: FloatBatch
    y: FloatBatch
    z: FloatBatch

    def __init__(self, x: FloatBatch, y: FloatBatch, z: FloatBatch) -> None: ...
    def __len__(self) -> int: ...


class Query(Generic[TEntity, TFilter]):
    def __init__(self) -> None: ...
    def get_component_signature(self) -> Signature: ...
    def get_excluded_component_signature(self) -> Signature: ...
    def matches(self, entity_signature: Signature) -> bool: ...
    def get_entities(self) -> set[Entity]: ...
    def add_entity(self, entity: Entity) -> None: ...
    def remove_entity(self, entity: Entity) -> None: ...
    def set_registry(self, registry: Registry) -> None: ...
    def fetch(self) -> TEntity: ...


class BatchQuery(Query[Entity, Any], Generic[*TBatchComponents]):
    def scalar(self, component_type: Type[Component], attribute_name: str) -> ScalarBatch: ...
    def vec2(self, component_type: Type[Component], attribute_name: str) -> Vec2Batch: ...
    def vec3(self, component_type: Type[Component], attribute_name: str) -> Vec3Batch: ...
    def entity_ids(self) -> NDArray[np.int64]: ...
    def _prepare_for_system_run(self) -> None: ...
    def _flush_after_system_run(self) -> None: ...


def get_annotations(function: Callable[..., Any]) -> OrderedDict[str, Any]: ...
def get_queries_from_arguments(args: Mapping[str, object]) -> list[tuple[str, object]]: ...
def get_queries_instance_from_arguments(args: Sequence[object]) -> list[Query[Any, Any]]: ...
def get_signed_query_arguments(function: Callable[..., Any]) -> OrderedDict[str, Any]: ...
def sign_queries(queries_signature: list[tuple[str, object]]) -> list[tuple[str, Query[Any, Any]]]: ...


__all__ = [
    "BatchQuery",
    "BoolMask",
    "Query",
    "ScalarBatch",
    "Vec2Batch",
    "Vec3Batch",
    "With",
    "Without",
    "get_annotations",
    "get_queries_from_arguments",
    "get_queries_instance_from_arguments",
    "get_signed_query_arguments",
    "sign_queries",
]from collections import OrderedDict
from typing import (Any, Callable, Generic, Iterable, Iterator, Mapping,
                    ParamSpec, Sequence, Type, TypeVar, overload)

from ..components import Component
from ..entities import Entity
from ..registry import Registry
from ..utils import Signature

TEntity = TypeVar("TEntity")
TFilter = TypeVar("TFilter")
P = ParamSpec("P")
C1 = TypeVar("C1", bound=Component)
C2 = TypeVar("C2", bound=Component)
C3 = TypeVar("C3", bound=Component)
C4 = TypeVar("C4", bound=Component)

class With(Generic[P]): ...
class Without(Generic[P]): ...

class Query(Generic[TEntity, TFilter]):
    _signature: Signature
    _entities: set[Entity]
    _kind: object
    _thread_id: int | None
    _registry: Registry | None

    def __init__(self) -> None: ...
    def get_component_signature(self) -> Signature: ...
    def get_excluded_component_signature(self) -> Signature: ...
    def get_entities(self) -> set[Entity]: ...
    def add_entity(self, entity: Entity) -> None: ...
    def remove_entity(self, entity: Entity) -> None: ...
    def __iter__(self) -> Iterable[Entity]: ...
    def set_registry(self, registry: Registry) -> None: ...
    def matches(self, entity_signature: Signature) -> bool: ...
    @overload
    def iter_components(self, component_type_1: Type[C1]) -> Iterator[tuple[C1]]: ...
    @overload
    def iter_components(
        self, component_type_1: Type[C1], component_type_2: Type[C2]
    ) -> Iterator[tuple[C1, C2]]: ...
    @overload
    def iter_components(
        self,
        component_type_1: Type[C1],
        component_type_2: Type[C2],
        component_type_3: Type[C3],
    ) -> Iterator[tuple[C1, C2, C3]]: ...
    @overload
    def iter_components(
        self,
        component_type_1: Type[C1],
        component_type_2: Type[C2],
        component_type_3: Type[C3],
        component_type_4: Type[C4],
    ) -> Iterator[tuple[C1, C2, C3, C4]]: ...
    @overload
    def iter_entities_components(
        self, component_type_1: Type[C1]
    ) -> Iterator[tuple[Entity, C1]]: ...
    @overload
    def iter_entities_components(
        self, component_type_1: Type[C1], component_type_2: Type[C2]
    ) -> Iterator[tuple[Entity, C1, C2]]: ...
    @overload
    def iter_entities_components(
        self,
        component_type_1: Type[C1],
        component_type_2: Type[C2],
        component_type_3: Type[C3],
    ) -> Iterator[tuple[Entity, C1, C2, C3]]: ...
    @overload
    def iter_entities_components(
        self,
        component_type_1: Type[C1],
        component_type_2: Type[C2],
        component_type_3: Type[C3],
        component_type_4: Type[C4],
    ) -> Iterator[tuple[Entity, C1, C2, C3, C4]]: ...
    def fetch(self) -> TEntity: ...

QuerySignature = list[tuple[str, Callable[[], Query[Any, Any]]]]

def get_signed_query_arguments(
    function: Callable[..., object],
) -> OrderedDict[str, Any]: ...
def sign_queries(
    queries_signature: QuerySignature,
) -> list[tuple[str, Query[Any, Any]]]: ...
def get_annotations(function: Callable[..., object]) -> OrderedDict[str, Any]: ...
def get_queries_from_arguments(
    args: Mapping[str, object],
) -> list[tuple[str, Callable[[], Query[Any, Any]]]]: ...
def get_queries_instance_from_arguments(
    args: Sequence[object],
) -> list[Query[Any, Any]]: ...

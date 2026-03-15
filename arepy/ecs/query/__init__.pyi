from collections import OrderedDict
from typing import (
    Any,
    Callable,
    Generic,
    Iterable,
    Iterator,
    Mapping,
    ParamSpec,
    Sequence,
    Type,
    TypeVar,
    overload,
)

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

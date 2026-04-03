from collections import OrderedDict
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Generic,
    Iterable,
    Iterator,
    List,
    Mapping,
    Optional,
    ParamSpec,
    Sequence,
    Type,
    TypeVar,
    Union,
    cast,
    get_type_hints,
)

from ..components import Component, ComponentIndex, ComponentPool
from ..constants import MAX_COMPONENTS
from ..exceptions import RegistryNotSetError
from ..utils import Signature

if TYPE_CHECKING:
    from ..entities import Entity
    from ..registry import Registry

TEntity = TypeVar("TEntity")
TFilter = TypeVar("TFilter")
P = ParamSpec("P")


class With(Generic[P]): ...


class Without(Generic[P]): ...


class Query(Generic[TEntity, TFilter]):
    """

    Query class to filter entities based on the components they have.

    Example:
    ```python
    from arepy.ecs.query import Query, EntityWith
    from arepy.bundle.components import Transform, Rigidbody2D

    def movement_system(query: Query[Entity, With[Transform, Rigidbody2D]]):
        for entity in query.get_entities():
            position = entity.get_component(Transform).position
            velocity = entity.get_component(Rigidbody2D).velocity

            position.x += velocity.x
            position.y += velocity.y
    ```


    TODO:
        Need to improve the query system, with TEntity we need to be able to get an specific entity
        I think we can improve the performance using only an entity with threads, so a system can get the entity and the system enqueue only the entity
        and the threads will process every entity(in chunks) instead of processing a loop of entities.
    """

    __slots__ = [
        "_signature",
        "_excluded_signature",
        "_entities",
        "_ordered_entities_cache",
        "_is_order_dirty",
        "_kind",
        "_thread_id",
        "_registry",
    ]

    def __init__(self) -> None:
        self._signature = Signature(MAX_COMPONENTS)
        self._excluded_signature = Signature(MAX_COMPONENTS)
        self._entities: set["Entity"] = set()
        self._ordered_entities_cache: tuple["Entity", ...] = ()
        self._is_order_dirty = False
        self._kind: object = None
        self._thread_id: Optional[int] = None
        self._registry: Optional["Registry"] = None

    def get_component_signature(self) -> Signature:
        return self._signature

    def get_excluded_component_signature(self) -> Signature:
        return self._excluded_signature

    def matches(self, entity_signature: Signature) -> bool:
        required_matches = self._signature.matches(entity_signature)
        excluded_bits = self._excluded_signature.get_bits()
        has_excluded_components = (entity_signature.get_bits() & excluded_bits).any()
        return required_matches and not has_excluded_components

    def get_entities(self) -> set["Entity"]:
        return self._entities

    def add_entity(self, entity: "Entity") -> None:
        if entity not in self._entities:
            self._entities.add(entity)
            self._is_order_dirty = True

    def remove_entity(self, entity: "Entity") -> None:
        try:
            self._entities.remove(entity)
            self._is_order_dirty = True
        except KeyError:
            pass

    def __iter__(self) -> Iterable["Entity"]:
        return iter(self._get_ordered_entities())

    def set_registry(self, registry: "Registry") -> None:
        self._registry = registry

    def iter_components(
        self, *component_types: Type[Component]
    ) -> Iterator[tuple[Component, ...]]:
        component_pools = self._get_component_pools(component_types)
        if component_pools is None:
            return

        for entity in self._get_ordered_entities():
            entity_id = entity.get_id() - 1
            components: list[Component] = []
            for component_pool in component_pools:
                component = component_pool.get(entity_id)
                if component is None:
                    break
                components.append(component)
            else:
                yield tuple(components)

    def iter_entities_components(
        self, *component_types: Type[Component]
    ) -> Iterator[tuple["Entity", *tuple[Component, ...]]]:
        component_pools = self._get_component_pools(component_types)
        if component_pools is None:
            return

        for entity in self._get_ordered_entities():
            entity_id = entity.get_id() - 1
            components: list[Component] = []
            for component_pool in component_pools:
                component = component_pool.get(entity_id)
                if component is None:
                    break
                components.append(component)
            else:
                yield (entity, *components)

    def _get_component_pools(
        self, component_types: Sequence[Type[Component]]
    ) -> list[ComponentPool[Component]] | None:
        if self._registry is None:
            raise RegistryNotSetError

        component_pools: list[ComponentPool[Component]] = []
        for component_type in component_types:
            component_id = ComponentIndex.get_id(component_type.__name__)
            if component_id > len(self._registry.component_pools):
                return None

            component_pool = self._registry.component_pools[component_id - 1]
            if component_pool is None:
                return None

            component_pools.append(cast(ComponentPool[Component], component_pool))
        return component_pools

    def _get_ordered_entities(self) -> tuple["Entity", ...]:
        if self._is_order_dirty:
            self._ordered_entities_cache = tuple(
                sorted(self._entities, key=lambda entity: entity.get_id())
            )
            self._is_order_dirty = False

        return self._ordered_entities_cache

    def fetch(self) -> TEntity: ...


def get_signed_query_arguments(function: Callable) -> OrderedDict[str, Any]:
    """Sign the query with the components that the function needs and return the arguments in order.

    note: in Python 3.14 we can use the new feature of the annotations module to get the annotations of a function.
    @see: https://docs.python.org/3.14/library/annotationlib.html
    """

    func_arguments = get_annotations(function)
    # remove return type from the arguments
    func_arguments.pop("return", None)

    queries_signature = get_queries_from_arguments(func_arguments)

    if not queries_signature:
        return func_arguments

    signed_queries = sign_queries(list(queries_signature))
    func_arguments.update(signed_queries)
    return func_arguments


QuerySignature = list[tuple[str, Callable[[], Query]]]


def sign_queries(
    queries_signature: QuerySignature,
) -> List[tuple[str, Query]]:
    """Sign the queries with the components that the query needs and return the queries in order."""
    signed_queries = []
    for name, query_signature in queries_signature:
        query_factory: Callable[[], Query] = cast(Callable[[], Query], query_signature)

        # Skip expensive type checking in production for performance
        if not hasattr(query_factory, "__args__"):
            raise TypeError(f"Query {query_factory} does not have args.")

        kind_of_result = query_factory.__args__[1]
        filter_groups = _extract_filter_groups(kind_of_result)
        query: Query = query_factory()
        query._kind = kind_of_result

        for filter_group in filter_groups:
            filter_origin = filter_group.__origin__
            component_signature = (
                query._signature if filter_origin is With else query._excluded_signature
            )
            for component_type in _extract_component_types(filter_group):
                if not issubclass(component_type, Component):
                    raise TypeError(
                        f"Query {name} has an invalid component type: {component_type.__name__}. "
                        "Make sure to use a valid component type."
                    )
                component_id = ComponentIndex.get_id(component_type.__name__)
                component_signature.set(component_id, True)

        signed_queries.append((name, query))
    return signed_queries


def _extract_filter_groups(filter_definition: object) -> tuple[object, ...]:
    if not hasattr(filter_definition, "__origin__"):
        raise TypeError(
            f"Invalid query kind: {filter_definition}. Expected `With` or `Without`."
        )

    filter_origin = getattr(filter_definition, "__origin__")
    if filter_origin in (With, Without):
        return (filter_definition,)

    if filter_origin is tuple:
        filter_groups = cast(
            tuple[object, ...], getattr(filter_definition, "__args__", ())
        )
        if not filter_groups:
            raise TypeError("Tuple query filters must not be empty.")
        for filter_group in filter_groups:
            if not hasattr(filter_group, "__origin__") or getattr(
                filter_group, "__origin__"
            ) not in (With, Without):
                raise TypeError(
                    f"Invalid query kind: {filter_group}. Expected `With` or `Without`."
                )
        return filter_groups

    raise TypeError(
        f"Invalid query kind: {filter_definition}. Expected `With` or `Without`."
    )


def _extract_component_types(filter_group: object) -> tuple[Type[Component], ...]:
    raw_args = cast(tuple[object, ...], getattr(filter_group, "__args__", ()))
    if len(raw_args) == 1 and isinstance(raw_args[0], (tuple, list)):
        return cast(tuple[Type[Component], ...], tuple(raw_args[0]))
    return cast(tuple[Type[Component], ...], raw_args)


def get_annotations(function: Callable) -> OrderedDict[str, Any]:
    """Get the annotations of a function in order.

    Uses typing.get_type_hints() to properly resolve string annotations
    that occur when using 'from __future__ import annotations'.
    """
    try:
        hints = get_type_hints(function)
        return OrderedDict(
            (key, hints[key]) for key in function.__annotations__ if key in hints
        )
    except Exception:
        return OrderedDict(function.__annotations__)


def get_queries_from_arguments(
    args: Mapping[str, object],
) -> list[tuple[str, Callable[[], Query]]]:
    """Get the queries from the arguments"""
    results = [
        (key, value)
        for key, value in args.items()
        if hasattr(value, "__qualname__") and value.__qualname__ == Query.__name__
    ]

    return cast(list[tuple[str, Callable[[], Query]]], results)


def get_queries_instance_from_arguments(args: Sequence[object]) -> list[Query]:
    """Get the instances of the queries from the arguments

    Args:
        args (dict[object, str]): the arguments of a function
    """
    results = [key for key in args if isinstance(key, Query)]
    return cast(list[Query], results)

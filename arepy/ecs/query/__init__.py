from collections import OrderedDict
from typing import (
    Any,
    Callable,
    Generic,
    Iterable,
    List,
    Mapping,
    Optional,
    ParamSpec,
    Sequence,
    Type,
    TypeVar,
    Union,
    cast,
)

from arepy.ecs.threading import ECS_LOCK

from ..components import Component, ComponentIndex
from ..constants import MAX_COMPONENTS
from ..utils import Signature

try:
    from .. import Entity
except ImportError:
    ...

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

    def __init__(self) -> None:
        self._signature = Signature(MAX_COMPONENTS)
        self._entities: set["Entity"] = set()
        self._kind: Union[With, Without] = None  # type: ignore
        self._thread_id: Optional[int] = None

    def get_component_signature(self) -> Signature:
        if self._kind is With and not self._signature.was_flipped:
            self._signature.flip()

        return self._signature

    def get_entities(self) -> set["Entity"]:
        return self._entities

    def add_entity(self, entity: "Entity") -> None:
        self._entities.add(entity)

    def remove_entity(self, entity: "Entity") -> None:
        self._entities.remove(entity)

    def __iter__(self) -> Iterable["Entity"]:
        return iter(self._entities)

    def fetch(self) -> TEntity: ...


def get_signed_query_arguments(function: Callable) -> OrderedDict[str, Any]:
    """Sign the query with the components that the function needs and return the arguments in order.

    note: in Python 3.14 we can use the new feature of the annotations module to get the annotations of a function.
    @see: https://docs.python.org/3.14/library/annotationlib.html
    """

    func_arguments = get_annotations(function)
    queries_signature = get_queries_from_arguments(func_arguments)

    if not queries_signature:
        return func_arguments

    signed_queries = sign_queries(queries_signature)
    func_arguments.update(signed_queries)
    return func_arguments


QuerySignature = list[tuple[str, Callable[[], Query]]]


def sign_queries(
    queries_signature: QuerySignature,
) -> List[tuple[str, Query]]:
    signed_queries = []
    for name, query_signature in queries_signature:
        query_factory: Callable[[], Query] = cast(Callable[[], Query], query_signature)
        kind_of_result = query_factory.__args__[1]
        required_components: tuple[Type[Component], ...] = kind_of_result.__args__[0]
        query: Query = query_factory()
        query._kind = kind_of_result
        for component_type in required_components:
            component_id = ComponentIndex.get_id(component_type.__name__)
            query._signature.set(component_id, True)
        signed_queries.append((name, query))

    return signed_queries


def get_annotations(function: Callable) -> OrderedDict[str, Any]:
    """Get the annotations of a function in order"""
    return OrderedDict(function.__annotations__)


def get_queries_from_arguments(
    args: Mapping[str, object]
) -> list[tuple[str, Callable[[], Query]]]:
    """Get the queries from the arguments"""
    results = [
        (key, value)
        for key, value in args.items()
        if value.__qualname__ == Query.__name__
    ]
    return cast(list[tuple[str, Callable[[], Query]]], results)


def get_queries_instance_from_arguments(args: Sequence[object]) -> list[Query]:
    """Get the instances of the queries from the arguments

    Args:
        args (dict[object, str]): the arguments of a function
    """
    results = [key for key in args if isinstance(key, Query)]
    return cast(list[Query], results)

from collections import OrderedDict
from typing import (
    Any,
    Callable,
    Generic,
    Iterable,
    Optional,
    ParamSpec,
    Type,
    TypeVar,
    Union,
    cast,
)

from ..components import Component, ComponentIndex
from ..constants import MAX_COMPONENTS
from ..utils import Signature

try:
    from .. import Entity
except ImportError:
    ...

T = TypeVar("T")
P = ParamSpec("P")


class EntityWith(Generic[P]): ...


class EntityWithout(Generic[P]): ...


class Query(Generic[T]):
    """

    Query class to filter entities based on the components they have.

    TODO: test this example and fix it if needed hehe :D
    Example:
    ```python
    from arepy.ecs.query import Query, EntityWith
    from arepy.bundle.components import Transform, Rigidbody2D

    def movement_system(query: Query[EntityWith[Transform, Rigidbody2D]]):
        for entity in query.get_entities():
            position = entity.get_component(Transform).position
            velocity = entity.get_component(Rigidbody2D).velocity

            position.x += velocity.x
            position.y += velocity.y
    ```
    """

    def __init__(self) -> None:
        self._signature = Signature(MAX_COMPONENTS)
        self._entities: set["Entity"] = set()
        self._kind: Union[EntityWith, EntityWithout] = None  # type: ignore
        self._thread_id: Optional[int] = None

    def get_component_signature(self) -> Signature:
        if self._kind is EntityWithout and not self._signature.was_flipped:
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


def make_query_signature(function: Callable) -> OrderedDict[object, Any]:
    """Sign the query with the components that the function needs."""

    func_arguments = get_args(function)
    query_signature = get_query_from_args(func_arguments, raw_query=True)

    if query_signature:
        raw_query: Query = cast(Query, query_signature)
        kind_of_result = raw_query.__args__[0]  # type: ignore
        required_components: tuple[Type[Component], ...] = kind_of_result.__args__[0]
        query = raw_query()  # type: ignore
        query._kind = kind_of_result

        query_signature_arguments = OrderedDict(
            [(query, func_arguments.pop(query_signature))]
        )
        query_signature_arguments.update(func_arguments)
        for component_type in required_components:
            component_id = ComponentIndex.get_id(component_type.__name__)
            query._signature.set(component_id, True)

    return query_signature_arguments


def get_args(function: Callable) -> OrderedDict[object, str]:
    return OrderedDict({value: key for (key, value) in OrderedDict(function.__annotations__).items()})  # type: ignore


def get_query_from_args(args: dict[object, str], raw_query: bool = False) -> Query:

    if raw_query:
        # When whe have a raw query(Annotation) search for it and return it
        result = [key for key in args if key.__qualname__ == Query.__name__][0]
        return cast(Query, result)

    for instance, _ in args.items():
        # When the instance is a Query, return it ^-^
        if isinstance(instance, Query):
            return instance
    raise Exception("Missing Query annotation")

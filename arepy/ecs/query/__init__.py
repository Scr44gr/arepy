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


def make_query_signature(function: Callable) -> OrderedDict[Any, str]:
    """Sign the query with the components that the function needs.

    note: in Python 3.14 we can use the new feature of the annotations module to get the annotations of a function.
    @see: https://docs.python.org/3.14/library/annotationlib.html
    """

    func_arguments = get_annotations(function)
    query_signature = get_query_from_args(func_arguments, raw_query=True)

    if not query_signature:
        return OrderedDict(func_arguments)

    raw_query: Callable[[], Query] = cast(Callable[[], Query], query_signature)
    kind_of_result = raw_query.__args__[1]
    required_components: tuple[Type[Component], ...] = kind_of_result.__args__[0]
    query: Query = raw_query()
    query._kind = kind_of_result

    # TODO:
    # if the query arg is not the first argument we will have problems
    # in order to fix this we should convert the func_arguments to a list and identify the query_signature index
    # after sign the query we should return the arguments in the correct order
    query_signature_arguments = OrderedDict(
        [(query, func_arguments.pop(query_signature))]
    )
    query_signature_arguments.update(func_arguments)
    for component_type in required_components:
        component_id = ComponentIndex.get_id(component_type.__name__)
        query._signature.set(component_id, True)

    return query_signature_arguments


def get_annotations(function: Callable) -> OrderedDict[Any, str]:
    """Get the annotations of a function in order"""
    return OrderedDict(
        {value: key for (key, value) in OrderedDict(function.__annotations__).items()}
    )


def get_query_from_args(
    args: dict[object, str], raw_query: bool = False
) -> Optional[Callable[[], Query] | Query]:

    # When whe have a raw query(Annotation) search for it and return it
    if raw_query:
        result = [key for key in args if key.__qualname__ == Query.__name__]
        if not result:
            return None
        return cast(Callable[[], Query], result[0])

    # When the instance is a Query, return it ^-^
    for instance, _ in args.items():
        if isinstance(instance, Query):
            return instance

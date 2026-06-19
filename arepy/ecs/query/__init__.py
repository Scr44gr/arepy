from collections import OrderedDict
from dataclasses import dataclass
from operator import attrgetter
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
    TypeVarTuple,
    cast,
    get_args,
    get_origin,
    get_type_hints,
)

import numpy as np
from numpy.typing import NDArray

from ...math.vec2 import Vec2
from ...math.vec3 import Vec3
from ..components import Component, ComponentIndex, ComponentPool, TComponent
from ..constants import MAX_COMPONENTS
from ..exceptions import RegistryNotSetError
from ..utils import Signature

if TYPE_CHECKING:
    from ..entities import Entity
    from ..registry import Registry

TEntity = TypeVar("TEntity")
TFilter = TypeVar("TFilter")
P = ParamSpec("P")
TBatchComponents = TypeVarTuple("TBatchComponents")
FloatBatch = NDArray[np.float64]
ScalarBatch = NDArray[Any]
BoolMask = NDArray[np.bool_]
_ENTITY_ID_GETTER = attrgetter("_id")
_X_GETTER = attrgetter("x")
_Y_GETTER = attrgetter("y")
_Z_GETTER = attrgetter("z")


class With(Generic[P]): ...


class Without(Generic[P]): ...


@dataclass(slots=True)
class _ResolvedRows:
    query_version: int
    component_revisions: tuple[int, ...]
    rows: tuple[tuple[object, ...], ...]


class Vec2Batch:
    __slots__ = ("x", "y")

    def __init__(self, x: FloatBatch, y: FloatBatch) -> None:
        self.x = x
        self.y = y

    def __len__(self) -> int:
        return len(self.x)


class Vec3Batch:
    __slots__ = ("x", "y", "z")

    def __init__(self, x: FloatBatch, y: FloatBatch, z: FloatBatch) -> None:
        self.x = x
        self.y = y
        self.z = z

    def __len__(self) -> int:
        return len(self.x)


@dataclass(slots=True)
class _ScalarWriteback:
    components: list[Component]
    accessor: "_BatchAttributeAccessor"
    values: ScalarBatch

    def flush(self) -> None:
        self.accessor.set_many(self.components, self.values.tolist())


@dataclass(frozen=True, slots=True)
class _BatchAttributeAccessor:
    get_one: Callable[[Component], object]
    get_many: Callable[[Sequence[Component]], list[object]]
    set_many: Callable[[Sequence[Component], Iterable[object]], None]
    bind_vec2_storage: Callable[[Sequence[Component], FloatBatch, FloatBatch], None]
    bind_vec3_storage: Callable[
        [Sequence[Component], FloatBatch, FloatBatch, FloatBatch], None
    ]
    bind_scalar_storage: Callable[[Sequence[Component], ScalarBatch], bool]
    scalar_storage_is_current: Callable[[Sequence[Component], ScalarBatch], bool]


_ATTRIBUTE_ACCESSORS: dict[str, _BatchAttributeAccessor] = {}


def _build_attribute_accessor(attribute_name: str) -> _BatchAttributeAccessor:
    getter = cast(Callable[[Component], object], attrgetter(attribute_name))

    def get_one(component: Component) -> object:
        return getter(component)

    def get_many(components: Sequence[Component]) -> list[object]:
        return list(map(getter, components))

    def set_many(
        components: Sequence[Component],
        values: Iterable[object],
    ) -> None:
        for component, value in zip(components, values):
            setattr(component, attribute_name, value)

    def bind_vec2_storage(
        components: Sequence[Component], x: FloatBatch, y: FloatBatch
    ) -> None:
        for index, component in enumerate(components):
            setattr(component, attribute_name, Vec2.from_storage(x, y, index))

    def bind_vec3_storage(
        components: Sequence[Component], x: FloatBatch, y: FloatBatch, z: FloatBatch
    ) -> None:
        for index, component in enumerate(components):
            setattr(component, attribute_name, Vec3.from_storage(x, y, z, index))

    def bind_scalar_storage(
        components: Sequence[Component], values: ScalarBatch
    ) -> bool:
        if not components:
            return True
        binder = getattr(type(components[0]), "_bind_scalar_storage", None)
        if binder is None:
            return False
        for index, component in enumerate(components):
            binder(component, attribute_name, values, index)
        return True

    def scalar_storage_is_current(
        components: Sequence[Component], values: ScalarBatch
    ) -> bool:
        if not components:
            return True
        checker = getattr(type(components[0]), "_uses_scalar_storage", None)
        return checker is not None and checker(
            components[0], attribute_name, values, 0
        )

    return _BatchAttributeAccessor(
        get_one=get_one,
        get_many=get_many,
        set_many=set_many,
        bind_vec2_storage=bind_vec2_storage,
        bind_vec3_storage=bind_vec3_storage,
        bind_scalar_storage=bind_scalar_storage,
        scalar_storage_is_current=scalar_storage_is_current,
    )


def _uses_storage(vector: object, storages: Sequence[object], index: int) -> bool:
    vector_storage = getattr(vector, "_storage", None)
    vector_index = getattr(vector, "_index", None)
    if vector_storage is None or vector_index != index:
        return False
    return len(vector_storage) == len(storages) and all(
        actual is expected for actual, expected in zip(vector_storage, storages)
    )


def _vec2_batch_is_current(
    components: Sequence[Component],
    accessor: _BatchAttributeAccessor,
    batch: Vec2Batch,
) -> bool:
    if not components:
        return True
    return _uses_storage(accessor.get_one(components[0]), (batch.x, batch.y), 0)


def _vec3_batch_is_current(
    components: Sequence[Component],
    accessor: _BatchAttributeAccessor,
    batch: Vec3Batch,
) -> bool:
    if not components:
        return True
    return _uses_storage(
        accessor.get_one(components[0]), (batch.x, batch.y, batch.z), 0
    )


def _refresh_vec2_batch(batch: Vec2Batch, vectors: Sequence[Vec2]) -> None:
    for index, vector in enumerate(vectors):
        batch.x[index] = vector.x
        batch.y[index] = vector.y


def _refresh_vec3_batch(batch: Vec3Batch, vectors: Sequence[Vec3]) -> None:
    for index, vector in enumerate(vectors):
        batch.x[index] = vector.x
        batch.y[index] = vector.y
        batch.z[index] = vector.z


def _get_attribute_accessor(attribute_name: str) -> _BatchAttributeAccessor:
    accessor = _ATTRIBUTE_ACCESSORS.get(attribute_name)
    if accessor is not None:
        return accessor

    accessor = _build_attribute_accessor(attribute_name)
    _ATTRIBUTE_ACCESSORS[attribute_name] = accessor
    return accessor


class Query(Generic[TEntity, TFilter]):
    """Filter entities based on their component signatures.

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
        "_version",
        "_component_rows_cache",
        "_entity_component_rows_cache",
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
        self._version = 0
        self._component_rows_cache: dict[tuple[Type[Component], ...], _ResolvedRows] = (
            {}
        )
        self._entity_component_rows_cache: dict[
            tuple[Type[Component], ...], _ResolvedRows
        ] = {}

    def get_component_signature(self) -> Signature:
        return self._signature

    def get_excluded_component_signature(self) -> Signature:
        return self._excluded_signature

    def matches(self, entity_signature: Signature) -> bool:
        return self._signature.matches(
            entity_signature
        ) and not self._excluded_signature.intersects(entity_signature)

    def get_entities(self) -> set["Entity"]:
        return self._entities

    def add_entity(self, entity: "Entity") -> None:
        entities = self._entities
        previous_size = len(entities)
        entities.add(entity)
        if len(entities) != previous_size:
            self._is_order_dirty = True
            self._version += 1

    def remove_entity(self, entity: "Entity") -> None:
        entities = self._entities
        previous_size = len(entities)
        entities.discard(entity)
        if len(entities) != previous_size:
            self._is_order_dirty = True
            self._version += 1

    def _sync_entities(
        self,
        dirty_entities: set["Entity"],
        entity_signatures: Sequence[Signature],
    ) -> None:
        matching_entities = {
            entity
            for entity in dirty_entities
            if self.matches(entity_signatures[entity._id - 1])
        }
        current_dirty_entities = self._entities.intersection(dirty_entities)
        if current_dirty_entities == matching_entities:
            return

        self._entities.difference_update(dirty_entities)
        self._entities.update(matching_entities)
        self._is_order_dirty = True
        self._version += 1

    def _remove_entities(self, entities: set["Entity"]) -> None:
        if not self._entities.isdisjoint(entities):
            self._entities.difference_update(entities)
            self._is_order_dirty = True
            self._version += 1

    def __iter__(self) -> Iterator["Entity"]:
        return iter(self._get_ordered_entities())

    def set_registry(self, registry: "Registry") -> None:
        self._registry = registry
        self._invalidate_iteration_cache()

    def iter_components(
        self, *component_types: Type[Component]
    ) -> Iterator[tuple[Component, ...]]:
        return iter(self._get_component_rows(component_types))

    def iter_entities_components(
        self, *component_types: Type[Component]
    ) -> Iterator[tuple["Entity", *tuple[Component, ...]]]:
        return iter(self._get_entity_component_rows(component_types))

    def _get_component_pools(
        self, component_types: Sequence[Type[Component]]
    ) -> list[ComponentPool[Component]] | None:
        if self._registry is None:
            raise RegistryNotSetError

        component_pools: list[ComponentPool[Component]] = []
        for component_type in component_types:
            component_id = ComponentIndex.get_type_id(component_type)
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
                sorted(self._entities, key=_ENTITY_ID_GETTER)
            )
            self._is_order_dirty = False

        return self._ordered_entities_cache

    def _get_component_rows(
        self, component_types: Sequence[Type[Component]]
    ) -> tuple[tuple[Component, ...], ...]:
        key = tuple(component_types)
        cached = self._component_rows_cache.get(key)
        component_revisions = self._get_registry_component_revisions(key)
        if (
            cached is not None
            and cached.query_version == self._version
            and cached.component_revisions == component_revisions
        ):
            return cast(tuple[tuple[Component, ...], ...], cached.rows)

        component_pools = self._get_component_pools(component_types)
        if component_pools is None:
            rows: tuple[tuple[Component, ...], ...] = ()
        else:
            component_arrays = [pool.get_all() for pool in component_pools]
            resolved_rows: list[tuple[Component, ...]] = []
            for entity in self._get_ordered_entities():
                entity_id = entity._id - 1
                components: list[Component] = []
                for component_array in component_arrays:
                    component = component_array[entity_id]
                    if component is None:
                        break
                    components.append(component)
                else:
                    resolved_rows.append(tuple(components))
            rows = tuple(resolved_rows)

        self._component_rows_cache[key] = _ResolvedRows(
            self._version,
            component_revisions,
            cast(tuple[tuple[object, ...], ...], rows),
        )
        return rows

    def _get_entity_component_rows(
        self, component_types: Sequence[Type[Component]]
    ) -> tuple[tuple["Entity", *tuple[Component, ...]], ...]:
        key = tuple(component_types)
        cached = self._entity_component_rows_cache.get(key)
        component_revisions = self._get_registry_component_revisions(key)
        if (
            cached is not None
            and cached.query_version == self._version
            and cached.component_revisions == component_revisions
        ):
            return cast(
                tuple[tuple["Entity", *tuple[Component, ...]], ...], cached.rows
            )

        component_pools = self._get_component_pools(component_types)
        if component_pools is None:
            rows: tuple[tuple["Entity", *tuple[Component, ...]], ...] = ()
        else:
            component_arrays = [pool.get_all() for pool in component_pools]
            resolved_rows: list[tuple["Entity", *tuple[Component, ...]]] = []
            for entity in self._get_ordered_entities():
                entity_id = entity._id - 1
                components: list[Component] = []
                for component_array in component_arrays:
                    component = component_array[entity_id]
                    if component is None:
                        break
                    components.append(component)
                else:
                    resolved_rows.append((entity, *components))
            rows = tuple(resolved_rows)

        self._entity_component_rows_cache[key] = _ResolvedRows(
            self._version,
            component_revisions,
            cast(tuple[tuple[object, ...], ...], rows),
        )
        return rows

    def _get_registry_component_revisions(
        self, component_types: Sequence[Type[Component]]
    ) -> tuple[int, ...]:
        if self._registry is None:
            raise RegistryNotSetError
        return self._registry.get_component_revisions(component_types)

    def _invalidate_iteration_cache(self) -> None:
        self._component_rows_cache.clear()
        self._entity_component_rows_cache.clear()

    def fetch(self) -> TEntity:
        raise NotImplementedError()


class BatchQuery(Query["Entity", Any], Generic[*TBatchComponents]):
    __slots__ = (
        "_component_cache",
        "_entity_id_batch",
        "_seen_query_version",
        "_seen_component_revisions",
        "_scalar_batches",
        "_vec2_batches",
        "_vec3_batches",
        "_scalar_writebacks",
        "_transient_scalar_keys",
    )

    def __init__(self) -> None:
        super().__init__()
        self._component_cache: dict[Type[Component], list[Component]] = {}
        self._entity_id_batch: NDArray[np.int64] | None = None
        self._seen_query_version = -1
        self._seen_component_revisions: tuple[int, ...] = ()
        self._scalar_batches: dict[
            tuple[Type[Component], str, object, bool, bool], ScalarBatch
        ] = {}
        self._vec2_batches: dict[tuple[Type[Component], str], Vec2Batch] = {}
        self._vec3_batches: dict[tuple[Type[Component], str], Vec3Batch] = {}
        self._scalar_writebacks: list[_ScalarWriteback] = []
        self._transient_scalar_keys: list[
            tuple[Type[Component], str, object, bool, bool]
        ] = []

    def scalar(
        self,
        component_type: Type[Component],
        attribute_name: str,
        *,
        dtype: object = None,
        writeback: bool = True,
        bind: bool = False,
    ) -> ScalarBatch:
        self._assert_component_allowed(component_type)

        if bind:
            writeback = False
        array_dtype = np.dtype(dtype) if dtype is not None else None
        key = (component_type, attribute_name, array_dtype, writeback, bind)
        components = self._get_batch_components(component_type)
        accessor = _get_attribute_accessor(attribute_name)
        cached = self._scalar_batches.get(key)
        if cached is not None:
            if not bind or accessor.scalar_storage_is_current(components, cached):
                return cached

        if array_dtype is None:
            values = np.asarray(accessor.get_many(components))
        else:
            values = np.fromiter(
                map(accessor.get_one, components),
                dtype=array_dtype,
                count=len(components),
            )
        if bind and not accessor.bind_scalar_storage(components, values):
            raise TypeError(
                f"Component {component_type.__name__}.{attribute_name} "
                "does not support bound scalar storage."
            )
        self._scalar_batches[key] = values
        if bind:
            return values
        self._transient_scalar_keys.append(key)
        if writeback:
            self._scalar_writebacks.append(
                _ScalarWriteback(components, accessor, values)
            )
        return values

    def vec2(self, component_type: Type[Component], attribute_name: str) -> Vec2Batch:
        self._assert_component_allowed(component_type)

        components = self._get_batch_components(component_type)
        accessor = _get_attribute_accessor(attribute_name)
        key = (component_type, attribute_name)
        cached = self._vec2_batches.get(key)
        if cached is not None:
            if _vec2_batch_is_current(components, accessor, cached):
                return cached

            vectors = cast(list[Vec2], accessor.get_many(components))
            if len(cached.x) == len(vectors):
                _refresh_vec2_batch(cached, vectors)
                accessor.bind_vec2_storage(components, cached.x, cached.y)
                return cached

        vectors = cast(list[Vec2], accessor.get_many(components))
        x = np.fromiter(map(_X_GETTER, vectors), dtype=np.float64, count=len(vectors))
        y = np.fromiter(map(_Y_GETTER, vectors), dtype=np.float64, count=len(vectors))
        batch = Vec2Batch(x, y)
        accessor.bind_vec2_storage(components, x, y)
        self._vec2_batches[key] = batch
        return batch

    def vec3(self, component_type: Type[Component], attribute_name: str) -> Vec3Batch:
        self._assert_component_allowed(component_type)

        components = self._get_batch_components(component_type)
        accessor = _get_attribute_accessor(attribute_name)
        key = (component_type, attribute_name)
        cached = self._vec3_batches.get(key)
        if cached is not None:
            if _vec3_batch_is_current(components, accessor, cached):
                return cached

            vectors = cast(list[Vec3], accessor.get_many(components))
            if len(cached.x) == len(vectors):
                _refresh_vec3_batch(cached, vectors)
                accessor.bind_vec3_storage(components, cached.x, cached.y, cached.z)
                return cached

        vectors = cast(list[Vec3], accessor.get_many(components))
        x = np.fromiter(map(_X_GETTER, vectors), dtype=np.float64, count=len(vectors))
        y = np.fromiter(map(_Y_GETTER, vectors), dtype=np.float64, count=len(vectors))
        z = np.fromiter(map(_Z_GETTER, vectors), dtype=np.float64, count=len(vectors))
        batch = Vec3Batch(x, y, z)
        accessor.bind_vec3_storage(components, x, y, z)
        self._vec3_batches[key] = batch
        return batch

    def entity_ids(self) -> NDArray[np.int64]:
        if self._entity_id_batch is None:
            self._entity_id_batch = np.asarray(
                [entity._id for entity in self._get_ordered_entities()],
                dtype=np.int64,
            )
        return self._entity_id_batch

    def components(self, component_type: TComponent) -> list[TComponent]:
        self._assert_component_allowed(component_type)
        return self._get_batch_components(component_type)

    def _prepare_for_system_run(self) -> None:
        if self._registry is None:
            raise RegistryNotSetError

        component_types = cast(tuple[Type[Component], ...], self._kind)
        component_revisions = self._registry.get_component_revisions(component_types)
        if (
            self._seen_query_version == self._version
            and self._seen_component_revisions == component_revisions
        ):
            return
        self._seen_query_version = self._version
        self._seen_component_revisions = component_revisions
        self._invalidate_cache()

    def _flush_after_system_run(self) -> None:
        for writeback in self._scalar_writebacks:
            writeback.flush()
        for key in self._transient_scalar_keys:
            self._scalar_batches.pop(key, None)
        self._transient_scalar_keys.clear()
        self._scalar_writebacks.clear()

    def _get_batch_components(self, component_type: Type[Component]) -> list[Component]:
        cached = self._component_cache.get(component_type)
        if cached is not None:
            return cached

        component_pools = self._get_component_pools((component_type,))
        if component_pools is None:
            return []

        component_pool = component_pools[0]
        component_array = component_pool.get_all()
        components: list[Component] = []
        for entity in self._get_ordered_entities():
            component = component_array[entity._id - 1]
            if component is not None:
                components.append(component)
        self._component_cache[component_type] = components
        return components

    def _invalidate_cache(self) -> None:
        self._component_cache.clear()
        self._entity_id_batch = None
        self._scalar_batches.clear()
        self._vec2_batches.clear()
        self._vec3_batches.clear()
        self._transient_scalar_keys.clear()
        self._scalar_writebacks.clear()

    def _assert_component_allowed(self, component_type: Type[Component]) -> None:
        if self._kind and component_type not in self._kind:
            raise TypeError(
                f"Component {component_type.__name__} is not part of this BatchQuery"
            )


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


QuerySignature = list[tuple[str, object]]


def sign_queries(
    queries_signature: QuerySignature,
) -> List[tuple[str, Query]]:
    """Sign the queries with the components that the query needs and return the queries in order."""
    signed_queries = []
    for name, query_signature in queries_signature:
        query_origin = _resolve_query_origin(query_signature)
        query_args = get_args(query_signature)
        if not query_args:
            try:
                query_args = query_signature.__args__
            except AttributeError:
                query_args = ()
        query_args_list = list(query_args)

        if query_origin is BatchQuery:
            if len(query_args_list) == 0:
                raise TypeError(f"BatchQuery {name} does not have component args.")

            batch_query = BatchQuery()
            component_types = cast(tuple[Type[Component], ...], tuple(query_args_list))
            batch_query._kind = component_types

            for component_type in component_types:
                if not issubclass(component_type, Component):
                    raise TypeError(
                        f"BatchQuery {name} has an invalid component type: {component_type}."
                    )
                component_id = ComponentIndex.get_type_id(component_type)
                batch_query._signature.set(component_id, True)

            signed_queries.append((name, batch_query))
            continue

        query_factory = cast(Callable[[], Query], query_origin)
        if len(query_args_list) < 2:
            raise TypeError(f"Query {query_factory} does not have args.")

        kind_of_result = query_args_list[1]
        filter_groups = _extract_filter_groups(kind_of_result)
        query: Query = query_factory()
        query._kind = kind_of_result

        for filter_group in filter_groups:
            filter_origin = get_origin(filter_group)
            if filter_origin is None:
                raise TypeError(
                    f"Invalid query kind: {filter_group}. Expected `With` or `Without`."
                )
            component_signature = (
                query._signature if filter_origin is With else query._excluded_signature
            )
            for component_type in _extract_component_types(filter_group):
                if not issubclass(component_type, Component):
                    raise TypeError(
                        f"Query {name} has an invalid component type: {component_type.__name__}. "
                        "Make sure to use a valid component type."
                    )
                component_id = ComponentIndex.get_type_id(component_type)
                component_signature.set(component_id, True)

        signed_queries.append((name, query))
    return signed_queries


def _resolve_query_origin(query_signature: object) -> type[Query] | type[BatchQuery]:
    query_origin = get_origin(query_signature)
    if query_origin in (Query, BatchQuery):
        return cast(type[Query] | type[BatchQuery], query_origin)
    if query_signature in (Query, BatchQuery):
        return cast(type[Query] | type[BatchQuery], query_signature)
    return Query


def _extract_filter_groups(filter_definition: object) -> tuple[object, ...]:
    filter_origin = get_origin(filter_definition)
    if filter_origin in (With, Without):
        return (filter_definition,)

    if filter_origin is tuple:
        filter_groups = cast(tuple[object, ...], get_args(filter_definition))
        if not filter_groups:
            raise TypeError("Tuple query filters must not be empty.")
        for filter_group in filter_groups:
            if get_origin(filter_group) not in (With, Without):
                raise TypeError(
                    f"Invalid query kind: {filter_group}. Expected `With` or `Without`."
                )
        return filter_groups

    raise TypeError(
        f"Invalid query kind: {filter_definition}. Expected `With` or `Without`."
    )


def _extract_component_types(filter_group: object) -> tuple[Type[Component], ...]:
    raw_args = cast(tuple[object, ...], get_args(filter_group))
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
) -> list[tuple[str, object]]:
    """Get the queries from the arguments"""
    results = [
        (key, value)
        for key, value in args.items()
        if value in (Query, BatchQuery) or get_origin(value) in (Query, BatchQuery)
    ]

    return results


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
]


def get_queries_instance_from_arguments(args: Sequence[object]) -> list[Query]:
    """Get the instances of the queries from the arguments

    Args:
        args (dict[object, str]): the arguments of a function
    """
    results = [key for key in args if isinstance(key, Query)]
    return cast(list[Query], results)

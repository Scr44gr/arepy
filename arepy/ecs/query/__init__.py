import keyword
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
from ..components import (
    Component,
    ComponentIndex,
    ComponentPool,
    TComponent,
    get_vector_attribute_epoch,
    watch_vector_attribute,
)
from ..constants import MAX_COMPONENTS
from ..exceptions import MaximumComponentsExceededError, RegistryNotSetError
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
_SCALAR_STORAGE_EPOCH = 0


class _QueryEntitySet(set["Entity"]):
    """A set that invalidates its owning query after public mutations."""

    __slots__ = ("_on_change",)

    def __init__(self, on_change: Callable[[], None]) -> None:
        super().__init__()
        self._on_change = on_change

    def _notify_if_size_changed(self, previous_size: int) -> None:
        if len(self) != previous_size:
            self._on_change()

    def add(self, element: "Entity") -> None:
        previous_size = len(self)
        super().add(element)
        self._notify_if_size_changed(previous_size)

    def discard(self, element: "Entity") -> None:
        previous_size = len(self)
        super().discard(element)
        self._notify_if_size_changed(previous_size)

    def remove(self, element: "Entity") -> None:
        super().remove(element)
        self._on_change()

    def pop(self) -> "Entity":
        element = super().pop()
        self._on_change()
        return element

    def clear(self) -> None:
        if not self:
            return
        super().clear()
        self._on_change()

    def update(self, *others: Iterable["Entity"]) -> None:
        previous_size = len(self)
        super().update(*others)
        self._notify_if_size_changed(previous_size)

    def difference_update(self, *others: Iterable[object]) -> None:
        previous_size = len(self)
        super().difference_update(*others)
        self._notify_if_size_changed(previous_size)

    def intersection_update(self, *others: Iterable[object]) -> None:
        previous_size = len(self)
        super().intersection_update(*others)
        self._notify_if_size_changed(previous_size)

    def symmetric_difference_update(self, other: Iterable["Entity"]) -> None:
        previous = set(self)
        super().symmetric_difference_update(other)
        if self != previous:
            self._on_change()

    def __ior__(self, other: Iterable["Entity"]):
        self.update(other)
        return self

    def __isub__(self, other: Iterable[object]):
        self.difference_update(other)
        return self

    def __iand__(self, other: Iterable[object]):
        self.intersection_update(other)
        return self

    def __ixor__(self, other: Iterable["Entity"]):
        self.symmetric_difference_update(other)
        return self

    def _replace_subset(
        self,
        removed: Iterable["Entity"],
        added: Iterable["Entity"],
    ) -> None:
        set.difference_update(self, removed)
        set.update(self, added)
        self._on_change()

    def _discard_many(self, entities: Iterable["Entity"]) -> None:
        set.difference_update(self, entities)
        self._on_change()


class With(Generic[P]): ...


class Without(Generic[P]): ...


@dataclass(slots=True)
class _ResolvedRows:
    query_version: int
    component_revisions: tuple[int, ...]
    rows: tuple[tuple[object, ...], ...]


class Vec2Batch:
    __slots__ = ("x", "y", "_storage_epoch", "_attribute_epoch")

    def __init__(self, x: FloatBatch, y: FloatBatch) -> None:
        self.x = x
        self.y = y
        self._storage_epoch = -1
        self._attribute_epoch = -1

    def __len__(self) -> int:
        return len(self.x)


class Vec3Batch:
    __slots__ = ("x", "y", "z", "_storage_epoch", "_attribute_epoch")

    def __init__(self, x: FloatBatch, y: FloatBatch, z: FloatBatch) -> None:
        self.x = x
        self.y = y
        self.z = z
        self._storage_epoch = -1
        self._attribute_epoch = -1

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


def _build_attribute_writeback(
    attribute_name: str,
) -> Callable[[Sequence[Component], Iterable[object]], None]:
    if attribute_name.isidentifier() and not keyword.iskeyword(attribute_name):
        namespace: dict[str, object] = {}
        code = compile(
            "def writeback(components, values):\n"
            "    for component, value in zip(components, values):\n"
            f"        component.{attribute_name} = value\n",
            "<arepy-batch-writer>",
            "exec",
        )
        exec(code, {}, namespace)
        return cast(
            Callable[[Sequence[Component], Iterable[object]], None],
            namespace["writeback"],
        )

    def writeback_dynamic(
        components: Sequence[Component], values: Iterable[object]
    ) -> None:
        for component, value in zip(components, values):
            component.__setattr__(attribute_name, value)

    return writeback_dynamic


def _build_attribute_accessor(attribute_name: str) -> _BatchAttributeAccessor:
    getter = cast(Callable[[Component], object], attrgetter(attribute_name))
    writeback = _build_attribute_writeback(attribute_name)

    def get_one(component: Component) -> object:
        return getter(component)

    def get_many(components: Sequence[Component]) -> list[object]:
        return list(map(getter, components))

    def bind_vec2_storage(
        components: Sequence[Component], x: FloatBatch, y: FloatBatch
    ) -> None:
        for index, component in enumerate(components):
            vector = getter(component)
            if not isinstance(vector, Vec2):
                raise TypeError(
                    f"{type(component).__name__}.{attribute_name} must be a Vec2."
                )
            vector._bind_storage(x, y, index)

    def bind_vec3_storage(
        components: Sequence[Component], x: FloatBatch, y: FloatBatch, z: FloatBatch
    ) -> None:
        for index, component in enumerate(components):
            vector = getter(component)
            if not isinstance(vector, Vec3):
                raise TypeError(
                    f"{type(component).__name__}.{attribute_name} must be a Vec3."
                )
            vector._bind_storage(x, y, z, index)

    def bind_scalar_storage(
        components: Sequence[Component], values: ScalarBatch
    ) -> bool:
        global _SCALAR_STORAGE_EPOCH
        if not components:
            return True
        component_type = cast(Any, type(components[0]))
        try:
            binder = component_type._bind_scalar_storage
        except AttributeError:
            return False
        _SCALAR_STORAGE_EPOCH += 1
        for index, component in enumerate(components):
            binder(component, attribute_name, values, index)
        return True

    def scalar_storage_is_current(
        components: Sequence[Component], values: ScalarBatch
    ) -> bool:
        if len(components) != len(values):
            return False
        if not components:
            return True
        component_type = cast(Any, type(components[0]))
        try:
            checker = component_type._uses_scalar_storage
        except AttributeError:
            return False
        return all(
            checker(component, attribute_name, values, index)
            for index, component in enumerate(components)
        )

    return _BatchAttributeAccessor(
        get_one=get_one,
        get_many=get_many,
        set_many=writeback,
        bind_vec2_storage=bind_vec2_storage,
        bind_vec3_storage=bind_vec3_storage,
        bind_scalar_storage=bind_scalar_storage,
        scalar_storage_is_current=scalar_storage_is_current,
    )


def _vec2_batch_is_current(
    components: Sequence[Component],
    accessor: _BatchAttributeAccessor,
    batch: Vec2Batch,
    component_type: Type[Component],
    attribute_name: str,
) -> bool:
    if len(components) != len(batch):
        return False
    storage_epoch = Vec2._get_storage_epoch()
    attribute_epoch = get_vector_attribute_epoch(component_type, attribute_name)
    if (
        batch._storage_epoch == storage_epoch
        and batch._attribute_epoch == attribute_epoch
    ):
        return True
    if not components:
        batch._storage_epoch = storage_epoch
        batch._attribute_epoch = attribute_epoch
        return True
    x = batch.x
    y = batch.y
    for index, component in enumerate(components):
        vector = accessor.get_one(component)
        if not isinstance(vector, Vec2):
            return False
        storage = vector._storage
        if (
            vector._index != index
            or storage is None
            or storage[0] is not x
            or storage[1] is not y
        ):
            return False
    batch._storage_epoch = storage_epoch
    batch._attribute_epoch = attribute_epoch
    return True


def _vec3_batch_is_current(
    components: Sequence[Component],
    accessor: _BatchAttributeAccessor,
    batch: Vec3Batch,
    component_type: Type[Component],
    attribute_name: str,
) -> bool:
    if len(components) != len(batch):
        return False
    storage_epoch = Vec3._get_storage_epoch()
    attribute_epoch = get_vector_attribute_epoch(component_type, attribute_name)
    if (
        batch._storage_epoch == storage_epoch
        and batch._attribute_epoch == attribute_epoch
    ):
        return True
    if not components:
        batch._storage_epoch = storage_epoch
        batch._attribute_epoch = attribute_epoch
        return True
    x = batch.x
    y = batch.y
    z = batch.z
    for index, component in enumerate(components):
        vector = accessor.get_one(component)
        if not isinstance(vector, Vec3):
            return False
        storage = vector._storage
        if (
            vector._index != index
            or storage is None
            or storage[0] is not x
            or storage[1] is not y
            or storage[2] is not z
        ):
            return False
    batch._storage_epoch = storage_epoch
    batch._attribute_epoch = attribute_epoch
    return True


def _refresh_vec2_batch(batch: Vec2Batch, vectors: Sequence[Vec2]) -> None:
    # Read every value before writing: retained vectors may still reference
    # these same arrays at different indices after query membership changes.
    batch.x[:] = list(map(_X_GETTER, vectors))
    batch.y[:] = list(map(_Y_GETTER, vectors))


def _refresh_vec3_batch(batch: Vec3Batch, vectors: Sequence[Vec3]) -> None:
    batch.x[:] = list(map(_X_GETTER, vectors))
    batch.y[:] = list(map(_Y_GETTER, vectors))
    batch.z[:] = list(map(_Z_GETTER, vectors))


def _validate_vector_values(
    vectors: Sequence[object],
    vector_type: type[Vec2] | type[Vec3],
    component_type: Type[Component],
    attribute_name: str,
) -> None:
    for vector in vectors:
        if not isinstance(vector, vector_type):
            raise TypeError(
                f"{component_type.__name__}.{attribute_name} must be a "
                f"{vector_type.__name__}."
            )


def _refresh_or_create_scalar_batch(
    cached: ScalarBatch | None,
    components: Sequence[Component],
    accessor: _BatchAttributeAccessor,
    array_dtype: np.dtype | None,
) -> ScalarBatch:
    if array_dtype is None:
        refreshed = np.asarray(accessor.get_many(components))
        if (
            cached is not None
            and cached.shape == refreshed.shape
            and cached.dtype == refreshed.dtype
        ):
            cached[...] = refreshed
            return cached
        return refreshed

    if (
        cached is not None
        and cached.ndim == 1
        and len(cached) == len(components)
        and cached.dtype == array_dtype
    ):
        cached[...] = accessor.get_many(components)
        return cached

    return np.fromiter(
        map(accessor.get_one, components),
        dtype=array_dtype,
        count=len(components),
    )


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
    from arepy.bundle.components import RigidBody2D, Transform
    from arepy.ecs import Entity, Query, With

    def movement_system(query: Query[Entity, With[Transform, RigidBody2D]]):
        for transform, rigid_body in query.iter_components(
            Transform,
            RigidBody2D,
        ):
            position = transform.position
            velocity = rigid_body.velocity

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
        self._signature = Signature(MAX_COMPONENTS + 1)
        self._excluded_signature = Signature(MAX_COMPONENTS + 1)
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
        self._entities: set["Entity"] = _QueryEntitySet(
            self._mark_entity_membership_changed
        )

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
        self._entities.add(entity)

    def remove_entity(self, entity: "Entity") -> None:
        self._entities.discard(entity)

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

        cast(_QueryEntitySet, self._entities)._replace_subset(
            dirty_entities, matching_entities
        )

    def _remove_entities(self, entities: set["Entity"]) -> None:
        if not self._entities.isdisjoint(entities):
            cast(_QueryEntitySet, self._entities)._discard_many(entities)

    def _mark_entity_membership_changed(self) -> None:
        self._ordered_entities_cache = ()
        self._is_order_dirty = True
        self._version += 1
        self._invalidate_iteration_cache()

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
            component_index = component_id - 1
            if component_index < 0 or component_index >= len(
                self._registry.component_pools
            ):
                return None

            component_pool = self._registry.component_pools[component_index]
            if (
                component_pool is None
                or component_pool._component_type is not component_type
            ):
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

    def fetch(self) -> Optional[TEntity]:
        return None


class BatchQuery(Query["Entity", Any], Generic[*TBatchComponents]):
    __slots__ = (
        "_component_cache",
        "_entity_id_batch",
        "_seen_query_version",
        "_seen_global_component_revision",
        "_seen_component_revisions",
        "_scalar_batches",
        "_scalar_storage_epochs",
        "_vec2_batches",
        "_vec3_batches",
        "_scalar_writebacks",
        "_scalar_writeback_cache",
        "_transient_scalar_keys",
    )

    def __init__(self) -> None:
        super().__init__()
        self._component_cache: dict[Type[Component], list[Component]] = {}
        self._entity_id_batch: NDArray[np.int64] | None = None
        self._seen_query_version = -1
        self._seen_global_component_revision = -1
        self._seen_component_revisions: tuple[int, ...] = ()
        self._scalar_batches: dict[
            tuple[Type[Component], str, object, bool, bool], ScalarBatch
        ] = {}
        self._scalar_storage_epochs: dict[
            tuple[Type[Component], str, object, bool, bool], int
        ] = {}
        self._vec2_batches: dict[tuple[Type[Component], str], Vec2Batch] = {}
        self._vec3_batches: dict[tuple[Type[Component], str], Vec3Batch] = {}
        self._scalar_writebacks: list[_ScalarWriteback] = []
        self._scalar_writeback_cache: dict[
            tuple[Type[Component], str, object, bool, bool], _ScalarWriteback
        ] = {}
        self._transient_scalar_keys: set[
            tuple[Type[Component], str, object, bool, bool]
        ] = set()

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
        if bind:
            if cached is not None:
                if self._scalar_storage_epochs.get(key) == _SCALAR_STORAGE_EPOCH:
                    return cached
                if accessor.scalar_storage_is_current(components, cached):
                    self._scalar_storage_epochs[key] = _SCALAR_STORAGE_EPOCH
                    return cached
        elif key in self._transient_scalar_keys and cached is not None:
            return cached

        values = _refresh_or_create_scalar_batch(
            cached,
            components,
            accessor,
            array_dtype,
        )
        if bind and not accessor.bind_scalar_storage(components, values):
            raise TypeError(
                f"Component {component_type.__name__}.{attribute_name} "
                "does not support bound scalar storage."
            )
        self._scalar_batches[key] = values
        if bind:
            self._scalar_storage_epochs[key] = _SCALAR_STORAGE_EPOCH
            return values
        self._transient_scalar_keys.add(key)
        if writeback:
            writeback_job = self._scalar_writeback_cache.get(key)
            if writeback_job is None:
                writeback_job = _ScalarWriteback(components, accessor, values)
                self._scalar_writeback_cache[key] = writeback_job
            else:
                writeback_job.components = components
                writeback_job.accessor = accessor
                writeback_job.values = values
            self._scalar_writebacks.append(writeback_job)
        return values

    def vec2(self, component_type: Type[Component], attribute_name: str) -> Vec2Batch:
        self._assert_component_allowed(component_type)

        components = self._get_batch_components(component_type)
        accessor = _get_attribute_accessor(attribute_name)
        key = (component_type, attribute_name)
        cached = self._vec2_batches.get(key)
        if cached is None:
            watch_vector_attribute(component_type, attribute_name)
        if cached is not None:
            if _vec2_batch_is_current(
                components, accessor, cached, component_type, attribute_name
            ):
                return cached

        raw_vectors = accessor.get_many(components)
        _validate_vector_values(raw_vectors, Vec2, component_type, attribute_name)
        vectors = cast(list[Vec2], raw_vectors)
        if cached is not None:
            if len(cached.x) == len(vectors):
                _refresh_vec2_batch(cached, vectors)
                accessor.bind_vec2_storage(components, cached.x, cached.y)
                cached._storage_epoch = Vec2._get_storage_epoch()
                cached._attribute_epoch = get_vector_attribute_epoch(
                    component_type, attribute_name
                )
                return cached

        x = np.fromiter(map(_X_GETTER, vectors), dtype=np.float64, count=len(vectors))
        y = np.fromiter(map(_Y_GETTER, vectors), dtype=np.float64, count=len(vectors))
        batch = Vec2Batch(x, y)
        accessor.bind_vec2_storage(components, x, y)
        batch._storage_epoch = Vec2._get_storage_epoch()
        batch._attribute_epoch = get_vector_attribute_epoch(
            component_type, attribute_name
        )
        self._vec2_batches[key] = batch
        return batch

    def vec3(self, component_type: Type[Component], attribute_name: str) -> Vec3Batch:
        self._assert_component_allowed(component_type)

        components = self._get_batch_components(component_type)
        accessor = _get_attribute_accessor(attribute_name)
        key = (component_type, attribute_name)
        cached = self._vec3_batches.get(key)
        if cached is None:
            watch_vector_attribute(component_type, attribute_name)
        if cached is not None:
            if _vec3_batch_is_current(
                components, accessor, cached, component_type, attribute_name
            ):
                return cached

        raw_vectors = accessor.get_many(components)
        _validate_vector_values(raw_vectors, Vec3, component_type, attribute_name)
        vectors = cast(list[Vec3], raw_vectors)
        if cached is not None:
            if len(cached.x) == len(vectors):
                _refresh_vec3_batch(cached, vectors)
                accessor.bind_vec3_storage(components, cached.x, cached.y, cached.z)
                cached._storage_epoch = Vec3._get_storage_epoch()
                cached._attribute_epoch = get_vector_attribute_epoch(
                    component_type, attribute_name
                )
                return cached

        x = np.fromiter(map(_X_GETTER, vectors), dtype=np.float64, count=len(vectors))
        y = np.fromiter(map(_Y_GETTER, vectors), dtype=np.float64, count=len(vectors))
        z = np.fromiter(map(_Z_GETTER, vectors), dtype=np.float64, count=len(vectors))
        batch = Vec3Batch(x, y, z)
        accessor.bind_vec3_storage(components, x, y, z)
        batch._storage_epoch = Vec3._get_storage_epoch()
        batch._attribute_epoch = get_vector_attribute_epoch(
            component_type, attribute_name
        )
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

        # A synchronous system may have raised before Registry could flush it.
        # Start every invocation with clean run-scoped writeback metadata while
        # retaining the NumPy buffers themselves for reuse.
        self._transient_scalar_keys.clear()
        self._scalar_writebacks.clear()

        global_revision = self._registry.get_component_revision()
        if (
            self._seen_query_version == self._version
            and self._seen_global_component_revision == global_revision
        ):
            return

        component_types = cast(tuple[Type[Component], ...], self._kind)
        component_revisions = self._registry.get_component_revisions(component_types)
        self._seen_global_component_revision = global_revision
        if (
            self._seen_query_version == self._version
            and self._seen_component_revisions == component_revisions
        ):
            return
        self._seen_query_version = self._version
        self._seen_component_revisions = component_revisions
        self._invalidate_cache()

    def _flush_after_system_run(self) -> None:
        try:
            for writeback in self._scalar_writebacks:
                writeback.flush()
        finally:
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
        for batch in self._vec2_batches.values():
            batch._storage_epoch = -1
            batch._attribute_epoch = -1
        for batch in self._vec3_batches.values():
            batch._storage_epoch = -1
            batch._attribute_epoch = -1
        self._scalar_storage_epochs.clear()
        self._scalar_writeback_cache.clear()
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
                if component_id > MAX_COMPONENTS:
                    raise MaximumComponentsExceededError(MAX_COMPONENTS)
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
                if component_id > MAX_COMPONENTS:
                    raise MaximumComponentsExceededError(MAX_COMPONENTS)
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

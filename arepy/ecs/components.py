from typing import (
    Any,
    Callable,
    Generic,
    List,
    Optional,
    ParamSpec,
    Type,
    TypeVar,
)
from weakref import WeakKeyDictionary, WeakSet


_VECTOR_ATTRIBUTE_EPOCHS: WeakKeyDictionary[type, dict[str, int]] = (
    WeakKeyDictionary()
)
_VECTOR_ATTRIBUTE_NAMES: set[str] = set()
_VECTOR_SETATTR_WATCHERS: WeakSet[type] = WeakSet()
_VECTOR_DELATTR_WATCHERS: WeakSet[type] = WeakSet()


def _bump_vector_attribute_epochs(instance: object, attribute_name: str) -> None:
    for component_type, attributes in tuple(_VECTOR_ATTRIBUTE_EPOCHS.items()):
        if attribute_name in attributes and isinstance(instance, component_type):
            attributes[attribute_name] += 1


def _find_special_method_owner(component_type: type, method_name: str) -> type:
    for base in component_type.__mro__:
        if method_name in base.__dict__:
            return base
    return object


def _install_vector_setattr_watcher(component_type: type) -> None:
    owner = _find_special_method_owner(component_type, "__setattr__")
    if owner in _VECTOR_SETATTR_WATCHERS:
        return

    original_setattr = component_type.__setattr__

    def watched_setattr(instance: object, name: str, value: object) -> None:
        original_setattr(instance, name, value)
        if name in _VECTOR_ATTRIBUTE_NAMES:
            _bump_vector_attribute_epochs(instance, name)

    type.__setattr__(component_type, "__setattr__", watched_setattr)
    _VECTOR_SETATTR_WATCHERS.add(component_type)


def _install_vector_delattr_watcher(component_type: type) -> None:
    owner = _find_special_method_owner(component_type, "__delattr__")
    if owner in _VECTOR_DELATTR_WATCHERS:
        return

    original_delattr = component_type.__delattr__

    def watched_delattr(instance: object, name: str) -> None:
        original_delattr(instance, name)
        if name in _VECTOR_ATTRIBUTE_NAMES:
            _bump_vector_attribute_epochs(instance, name)

    type.__setattr__(component_type, "__delattr__", watched_delattr)
    _VECTOR_DELATTR_WATCHERS.add(component_type)


def watch_vector_attribute(component_type: type, attribute_name: str) -> int:
    """Track replacements of a component attribute used by a vector batch."""

    attributes = _VECTOR_ATTRIBUTE_EPOCHS.setdefault(component_type, {})
    epoch = attributes.setdefault(attribute_name, 0)
    _VECTOR_ATTRIBUTE_NAMES.add(attribute_name)
    _install_vector_setattr_watcher(component_type)
    _install_vector_delattr_watcher(component_type)
    return epoch


def get_vector_attribute_epoch(component_type: type, attribute_name: str) -> int:
    attributes = _VECTOR_ATTRIBUTE_EPOCHS.get(component_type)
    if attributes is None:
        return 0
    return attributes.get(attribute_name, 0)


class ComponentIndex:
    """A class to manage component IDs for classes with the same name."""

    __id_counters: dict[str, int] = {}
    __last_id = 0

    @classmethod
    def get_id(cls, class_name: str) -> int:
        component_id = cls.__id_counters.get(class_name)
        if component_id is None:
            cls.__last_id += 1
            component_id = cls.__last_id
            cls.__id_counters[class_name] = component_id
        return component_id

    @classmethod
    def get_type_id(cls, component_type: type) -> int:
        component_id = component_type.__dict__.get("_arepy_component_id")
        if component_id is None:
            component_id = cls.get_id(component_type.__name__)
            setattr(component_type, "_arepy_component_id", component_id)
        return component_id

    @classmethod
    def try_get_type_id(cls, component_type: type) -> Optional[int]:
        """Return an existing component ID without allocating a new one."""

        component_id = component_type.__dict__.get("_arepy_component_id")
        if component_id is not None:
            return component_id
        return cls.__id_counters.get(component_type.__name__)


class Component:
    """A component is a data container that can be attached to an entity.

    Components are used to store data that is relevant to an entity.
    """

    def __init__(self, *args, **kwargs):
        self.id = ComponentIndex.get_type_id(type(self))

    def get_id(self) -> int:
        """Return the unique id of the component."""
        try:
            return self.id
        except AttributeError:
            # Some existing component classes intentionally skip
            # ``Component.__init__``; keep them usable without changing the
            # established behavior for instances that expose ``id``.
            return ComponentIndex.get_type_id(type(self))


TComponent = TypeVar("TComponent", bound=Component)
PComponent = ParamSpec("PComponent")


class IComponentPool:
    """An interface for component pools."""

    def is_empty(self) -> bool:
        """Return whether the component pool is empty."""
        raise NotImplementedError

    def set(self, entity_id: int, component: Any) -> None:
        """Set a component to the pool."""
        raise NotImplementedError

    def remove(self, entity_id: int) -> None:
        """Remove a component from the pool."""
        raise NotImplementedError

    def get(self, index: int) -> Optional[Any]:
        """Get a component from the pool."""
        raise NotImplementedError

    def get_all(self) -> List[Any]:
        """Get all components from the pool."""
        raise NotImplementedError

    def resize_with(self, size: int, fill: Callable[[], Any]):
        """Resize the component pool with a fill function."""
        raise NotImplementedError


class ComponentPool(Generic[TComponent], IComponentPool):
    """A pool of components of a specific type.

    This class is used to store components of a specific type.
    """

    def __init__(self, component_type: Type[TComponent]):
        self._component_type = component_type
        self._components: List[Optional[TComponent]] = list()

    def is_empty(self) -> bool:
        return all(component is None for component in self._components)

    def set(self, entity_id: int, component: TComponent) -> None:
        self._components[entity_id] = component

    def remove(self, entity_id: int):
        self._components[entity_id] = None

    def get(self, index: int) -> Optional[TComponent]:
        return self._components[index]

    def get_all(self) -> List[Optional[TComponent]]:
        return self._components

    def extend(self, components: List[Optional[TComponent]]):
        self._components.extend(components)

    def resize_with(self, size: int, fill: Callable[[], Optional[TComponent]]):
        for _ in range(size - len(self._components)):
            self._components.append(fill())

    def __len__(self):
        return len(self._components)

    def __iter__(self):
        return iter(self._components)

    def __contains__(self, item):
        return item in self._components

    def __getitem__(self, item):
        return self._components[item]

    def __setitem__(self, key, value):
        self._components[key] = value

    def __delitem__(self, key):
        del self._components[key]

    def __repr__(self):
        return f"ComponentPool({self._component_type})"

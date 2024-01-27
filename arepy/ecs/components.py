from typing import Any, Callable, Generic, List, Optional, ParamSpec, Type, TypeVar


class ComponentIndex:
    """A class to manage component IDs for classes with the same name."""

    __id_counters: dict = {}
    __last_insert: Optional[str] = None

    @classmethod
    def get_id(cls, class_name):
        internal_class_name = f"{class_name}_{id(cls)}"
        if not internal_class_name in cls.__id_counters:
            counter = 0
            if cls.__last_insert:
                counter = cls.__id_counters[cls.__last_insert]
            cls.__id_counters[internal_class_name] = counter + 1
            cls.__last_insert = internal_class_name
        return cls.__id_counters[internal_class_name]


class Component:
    """A component is a data container that can be attached to an entity.

    Components are used to store data that is relevant to an entity.
    """

    def __init__(self, *args, **kwargs):
        class_name = type(self).__name__
        self.id = ComponentIndex.get_id(class_name)

    def get_id(self) -> int:
        """Return the unique id of the component."""
        return self.id


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
        # default size == 32
        self._component_type = component_type
        self._components: List[Optional[TComponent]] = list()

    def is_empty(self) -> bool:
        return len(self._components) == 0

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

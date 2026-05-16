from typing import Optional

from ...ecs import Component
from ._field_views import InternedStringTable

_MODEL_NAMES = InternedStringTable()
_MESH_NAMES = InternedStringTable()
_MATERIAL_NAMES = InternedStringTable()


class Model3D(Component):
    """Component that holds a reference to a 3D model."""

    model_name_handle: int
    material_name_handle: int

    def __init__(self, model_name: str, material_name: Optional[str] = None):
        super().__init__()
        self.model_name = model_name
        self.material_name = material_name

    @property
    def model_name(self) -> object:
        return _MODEL_NAMES.resolve(self.model_name_handle)

    @model_name.setter
    def model_name(self, value: str) -> None:
        self.model_name_handle = _MODEL_NAMES.intern(value)

    @property
    def material_name(self) -> object:
        return _MATERIAL_NAMES.resolve(self.material_name_handle)

    @material_name.setter
    def material_name(self, value: Optional[str]) -> None:
        self.material_name_handle = _MATERIAL_NAMES.intern(value)


class Mesh3D(Component):
    """Component that holds a reference to a 3D mesh."""

    mesh_name_handle: int
    material_name_handle: int

    def __init__(self, mesh_name: str, material_name: Optional[str] = None):
        super().__init__()
        self.mesh_name = mesh_name
        self.material_name = material_name

    @property
    def mesh_name(self) -> object:
        return _MESH_NAMES.resolve(self.mesh_name_handle)

    @mesh_name.setter
    def mesh_name(self, value: str) -> None:
        self.mesh_name_handle = _MESH_NAMES.intern(value)

    @property
    def material_name(self) -> object:
        return _MATERIAL_NAMES.resolve(self.material_name_handle)

    @material_name.setter
    def material_name(self, value: Optional[str]) -> None:
        self.material_name_handle = _MATERIAL_NAMES.intern(value)

from ...ecs import Component
from ._field_views import InternedStringTable

_MODEL_NAMES = InternedStringTable()
_MESH_NAMES = InternedStringTable()
_MATERIAL_NAMES = InternedStringTable()


class Model3D(Component):
    """Component that holds a reference to a 3D model."""

    model_name_handle: int = 0
    material_name_handle: int = 0


class Mesh3D(Component):
    """Component that holds a reference to a 3D mesh."""

    mesh_name_handle: int = 0
    material_name_handle: int = 0


def make_model_3d(model_name: str, material_name: str | None = None) -> Model3D:
    return Model3D(
        model_name_handle=_MODEL_NAMES.intern(model_name),
        material_name_handle=_MATERIAL_NAMES.intern(material_name),
    )


def resolve_model_name(model: Model3D) -> str | None:
    resolved = _MODEL_NAMES.resolve(model.model_name_handle)
    return resolved if isinstance(resolved, str) else None


def resolve_model_material_name(model: Model3D) -> str | None:
    resolved = _MATERIAL_NAMES.resolve(model.material_name_handle)
    return resolved if isinstance(resolved, str) else None


def make_mesh_3d(mesh_name: str, material_name: str | None = None) -> Mesh3D:
    return Mesh3D(
        mesh_name_handle=_MESH_NAMES.intern(mesh_name),
        material_name_handle=_MATERIAL_NAMES.intern(material_name),
    )


def resolve_mesh_name(mesh: Mesh3D) -> str | None:
    resolved = _MESH_NAMES.resolve(mesh.mesh_name_handle)
    return resolved if isinstance(resolved, str) else None


def resolve_mesh_material_name(mesh: Mesh3D) -> str | None:
    resolved = _MATERIAL_NAMES.resolve(mesh.material_name_handle)
    return resolved if isinstance(resolved, str) else None

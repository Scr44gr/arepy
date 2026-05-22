from ...ecs import Component
from ._field_views import InternedStringTable

_MATERIAL_NAMES = InternedStringTable()


class Material3D(Component):
    """Component that holds material properties for 3D rendering."""

    material_name_handle: int = 0
    albedo_r: float = 1.0
    albedo_g: float = 1.0
    albedo_b: float = 1.0
    albedo_a: float = 1.0
    metallic: float = 0.0
    roughness: float = 0.5
    ao: float = 1.0
    emission_r: float = 0.0
    emission_g: float = 0.0
    emission_b: float = 0.0


def make_material_3d(
    material_name: str,
    albedo_color: tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0),
    metallic: float = 0.0,
    roughness: float = 0.5,
    ao: float = 1.0,
    emission: tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> Material3D:
    return Material3D(
        material_name_handle=_MATERIAL_NAMES.intern(material_name),
        albedo_r=albedo_color[0],
        albedo_g=albedo_color[1],
        albedo_b=albedo_color[2],
        albedo_a=albedo_color[3],
        metallic=metallic,
        roughness=roughness,
        ao=ao,
        emission_r=emission[0],
        emission_g=emission[1],
        emission_b=emission[2],
    )


def resolve_material_name(material: Material3D) -> str | None:
    resolved = _MATERIAL_NAMES.resolve(material.material_name_handle)
    return resolved if isinstance(resolved, str) else None

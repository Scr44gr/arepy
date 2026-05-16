from ...ecs import Component
from ._field_views import InternedStringTable, assign_fields, field_tuple

_MATERIAL_NAMES = InternedStringTable()


class Material3D(Component):
    """Component that holds material properties for 3D rendering."""

    material_name_handle: int
    albedo_r: float
    albedo_g: float
    albedo_b: float
    albedo_a: float
    metallic: float
    roughness: float
    ao: float
    emission_r: float
    emission_g: float
    emission_b: float

    def __init__(
        self,
        material_name: str,
        albedo_color: tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0),
        metallic: float = 0.0,
        roughness: float = 0.5,
        ao: float = 1.0,
        emission: tuple[float, float, float] = (0.0, 0.0, 0.0),
    ):
        super().__init__()
        self.material_name = material_name
        self.albedo_color = albedo_color
        self.metallic = metallic
        self.roughness = roughness
        self.ao = ao  # Ambient occlusion
        self.emission = emission

    @property
    def material_name(self) -> object:
        return _MATERIAL_NAMES.resolve(self.material_name_handle)

    @material_name.setter
    def material_name(self, value: str) -> None:
        self.material_name_handle = _MATERIAL_NAMES.intern(value)

    @property
    def albedo_color(self) -> tuple[object, object, object, object]:
        return field_tuple(self, "albedo_r", "albedo_g", "albedo_b", "albedo_a")

    @albedo_color.setter
    def albedo_color(self, value: tuple[float, float, float, float]) -> None:
        assign_fields(self, value, "albedo_r", "albedo_g", "albedo_b", "albedo_a")

    @property
    def emission(self) -> tuple[object, object, object]:
        return field_tuple(self, "emission_r", "emission_g", "emission_b")

    @emission.setter
    def emission(self, value: tuple[float, float, float]) -> None:
        assign_fields(self, value, "emission_r", "emission_g", "emission_b")

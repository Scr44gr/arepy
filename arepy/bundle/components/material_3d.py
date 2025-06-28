from ...ecs import Component


class Material3D(Component):
    """Component that holds material properties for 3D rendering."""

    def __init__(
        self,
        material_name: str,
        albedo_color: tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0),
        metallic: float = 0.0,
        roughness: float = 0.5,
        ao: float = 1.0,
        emission: tuple[float, float, float] = (0.0, 0.0, 0.0),
    ):
        self.material_name = material_name
        self.albedo_color = albedo_color
        self.metallic = metallic
        self.roughness = roughness
        self.ao = ao  # Ambient occlusion
        self.emission = emission

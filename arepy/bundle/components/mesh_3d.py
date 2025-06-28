from typing import Optional

from ...ecs import Component


class Model3D(Component):
    """Component that holds a reference to a 3D model."""

    def __init__(self, model_name: str, material_name: Optional[str] = None):
        self.model_name = model_name
        self.material_name = material_name


class Mesh3D(Component):
    """Component that holds a reference to a 3D mesh."""

    def __init__(self, mesh_name: str, material_name: Optional[str] = None):
        self.mesh_name = mesh_name
        self.material_name = material_name

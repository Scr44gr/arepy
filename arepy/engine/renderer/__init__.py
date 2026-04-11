from dataclasses import dataclass
from enum import Enum
from typing import Sequence, TypeAlias


class TextureFilter(Enum):
    NEAREST = 0
    BILINEAR = 1
    TRILINEAR = 2


class ShaderUniformType(Enum):
    FLOAT = 0
    VEC2 = 1
    VEC3 = 2
    VEC4 = 3
    INT = 4
    IVEC2 = 5
    IVEC3 = 6
    IVEC4 = 7
    SAMPLER2D = 8
    MAT4 = 9


class ArepyTexture:
    def __init__(
        self,
        texture_id: int,
        size: tuple[int, int],
        filter: TextureFilter = TextureFilter.NEAREST,
    ):
        self.texture_id = texture_id
        self._texture_size = size
        self._ref_texture: object = None
        self._ref_render_texture: object = None
        self._filter = filter

    def get_size(self) -> tuple[int, int]:
        return self._texture_size

    def unload(self) -> None: ...


class ArepyShader:
    def __init__(self, shader_id: int):
        self.shader_id = shader_id
        self._ref_shader: object = None
        self._uniform_locations: dict[str, int] = {}

    def unload(self) -> None: ...


ShaderScalar: TypeAlias = int | float
ShaderSequence: TypeAlias = Sequence[int | float]
ShaderValue: TypeAlias = ShaderScalar | ShaderSequence | ArepyTexture


class ArepyFont:
    def __init__(
        self,
        base_size: int,
    ):
        self.base_size = base_size
        self._ref_font: object = None

    def unload(self) -> None: ...


@dataclass(slots=True)
class Rect:
    x: float
    y: float
    width: int
    height: int

    def to_tuple(self) -> tuple[float, float, int, int]:
        return (self.x, self.y, self.width, self.height)


@dataclass(slots=True)
class Color:
    r: int
    g: int
    b: int
    a: int

    def normalize(self) -> tuple[float, float, float, float]:
        return (self.r / 255, self.g / 255, self.b / 255, self.a / 255)

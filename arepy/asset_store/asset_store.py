import ctypes
from enum import Enum
from typing import Dict

import numpy as np
import OpenGL.GL as gl
from freetype import Face
from PIL import Image


class TextureFilter(Enum):
    NEAREST = 0
    LINEAR = 1
    MIPMAP = 2


class AssetStore:
    textures: Dict[str, int] = dict()
    fonts: Dict[str, Face] = dict()

    def load_texture(
        self,
        name: str,
        path: str,
        filter: TextureFilter = TextureFilter.LINEAR,
    ) -> None:
        texture = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, texture)

        image = np.asarray(Image.open(path), dtype=np.uint8)
        image_data_ptr = image.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8))
        gl.glPixelStorei(gl.GL_UNPACK_ALIGNMENT, 1)

        gl.glBindTexture(gl.GL_TEXTURE_2D, texture)
        gl.glTexImage2D(
            gl.GL_TEXTURE_2D,
            0,
            gl.GL_RGBA,  # how the texture is stored in memory
            image.shape[1],
            image.shape[0],
            0,
            gl.GL_RGBA,  # the format of the input
            gl.GL_UNSIGNED_BYTE,  # the data type of the input
            image_data_ptr,
        )

        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
        match filter:
            case TextureFilter.NEAREST:
                gl.glTexParameteri(
                    gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST
                )
                gl.glTexParameteri(
                    gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST
                )
            case TextureFilter.LINEAR:
                gl.glTexParameteri(
                    gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR
                )
                gl.glTexParameteri(
                    gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR
                )
            case TextureFilter.MIPMAP:
                gl.glTexParameteri(
                    gl.GL_TEXTURE_2D,
                    gl.GL_TEXTURE_MIN_FILTER,
                    gl.GL_LINEAR_MIPMAP_LINEAR,
                )
                gl.glTexParameteri(
                    gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR
                )

        gl.glBindTexture(gl.GL_TEXTURE_2D, 0)
        self.textures[name] = texture

    def load_font(self, name: str, path: str, size: int) -> None:
        font = Face(path)
        font.set_pixel_sizes(0, size)
        self.fonts[name] = font

    def get_texture(self, name: str) -> int:
        return self.textures[name]

    def get_font(self, name: str) -> Face:
        return self.fonts[name]

from ctypes import c_uint32
from dataclasses import dataclass, field
from time import time
from typing import Optional

import numpy as np
import OpenGL.GL as gl
from PIL import Image

from .. import ArepyTexture, BaseRenderer
from .shaders import compile_default_shader
from .utils import (DEFAULT_TEXTURE_COORDS, get_line_rgba_data,
                    get_texture_coordinates, is_outside_screen)

MODEL = np.array([1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1], dtype=np.float32)


class Vertex:
    def __init__(
        self,
        position: tuple[float, float],
        color: tuple[float, float, float, float],
        texture_coords: tuple[float, float],
        texture_id: float,
    ):
        self.position = position
        self.color = color
        self.texture_coords = texture_coords
        self.texture_id = texture_id

        self.data = np.array(
            [*self.position, *self.color, *self.texture_coords, self.texture_id],
            dtype=np.float32,
        )


@dataclass
class RendererData:
    index_data: np.ndarray
    index_count: int = field(default=0, init=False)
    texture_vbo: Optional[int]
    texture_vao: Optional[int]
    texture_ibo: Optional[int]
    texture_buffer: Optional[np.ndarray]
    texture_buffer_index: Optional[int]
    # Textures
    white_texture: int = field(default=0, init=False)
    white_texture_slot: int = field(default=0, init=False)
    texture_slots: list[int] = field(default_factory=lambda: [0] * 32, init=False)
    texture_slot_index: int = field(default=1, init=False)


class OpenGLRenderer(BaseRenderer):
    MAX_TRIANGLES = 1000
    MAX_VERTEX_COUNT = MAX_TRIANGLES * 4
    MAX_INDEX_COUNT = MAX_TRIANGLES * 6
    MAX_TEXTURE_SLOTS = 32

    def __init__(self, screen_size: tuple[int, int], window_size: tuple[int, int]):
        super().__init__(screen_size, window_size)

        self.gl_init()

    def gl_init(self):
        self.VBO = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.VBO)

        gl.glBufferData(
            gl.GL_ARRAY_BUFFER,
            self.MAX_VERTEX_COUNT
            * Vertex((0.0, 0.0), (1.0, 1.0, 1.0, 1.0), (0.0, 0.0), 0.0).data.nbytes,
            None,
            gl.GL_DYNAMIC_DRAW,
        )

        self.VAO = gl.glGenVertexArrays(1)
        gl.glBindVertexArray(self.VAO)
        gl.glEnableVertexAttribArray(0)  # position is vec2
        stride = Vertex((0.0, 0.0), (1.0, 1.0, 1.0, 1.0), (0.0, 0.0), 0.0).data.nbytes
        gl.glVertexAttribPointer(
            0,
            2,
            gl.GL_FLOAT,
            gl.GL_FALSE,
            stride,
            gl.ctypes.c_void_p(0),
        )
        # Color is 4 floats
        gl.glEnableVertexAttribArray(1)
        gl.glVertexAttribPointer(
            1,
            4,
            gl.GL_FLOAT,
            gl.GL_FALSE,
            stride,
            gl.ctypes.c_void_p(2 * 4),
        )
        # Texture coords is vec2
        gl.glEnableVertexAttribArray(2)
        gl.glVertexAttribPointer(
            2,
            2,
            gl.GL_FLOAT,
            gl.GL_FALSE,
            stride,
            gl.ctypes.c_void_p(6 * 4),
        )
        # Texture index is a float
        gl.glEnableVertexAttribArray(3)
        gl.glVertexAttribPointer(
            3,
            1,
            gl.GL_FLOAT,
            gl.GL_FALSE,
            stride,
            gl.ctypes.c_void_p(8 * 4),
        )
        gl.glBindVertexArray(0)
        indices = np.zeros(self.MAX_INDEX_COUNT, dtype=np.uint32)
        offset = 0
        for i in range(0, self.MAX_INDEX_COUNT, 6):
            indices[i + 0] = offset + 0
            indices[i + 1] = offset + 1
            indices[i + 2] = offset + 2

            indices[i + 3] = offset + 0
            indices[i + 4] = offset + 2
            indices[i + 5] = offset + 3
            offset += 4
        self.IBO = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.IBO)
        gl.glBufferData(
            gl.GL_ELEMENT_ARRAY_BUFFER,
            self.MAX_INDEX_COUNT * 4,
            indices,
            gl.GL_STATIC_DRAW,
        )

        self.setup_shader()

        # Enable blending
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

        self.renderer_data = RendererData(
            texture_vbo=self.VBO,
            texture_vao=self.VAO,
            texture_ibo=self.IBO,
            texture_buffer_index=0,
            index_data=indices,
            texture_buffer=np.array(
                [Vertex((0.0, 0.0), (0.0, 0.0, 0.0, 1.0), (0.0, 0.0), 0.0).data]
                * self.MAX_VERTEX_COUNT,
                dtype=np.float32,
            ),
        )
        assert self.renderer_data.texture_buffer is not None

        self.renderer_data.white_texture = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.renderer_data.white_texture)
        white_texture_data = np.array([255, 255, 255, 255], dtype=np.uint8)
        gl.glTexImage2D(
            gl.GL_TEXTURE_2D,
            0,
            gl.GL_RGBA,
            1,
            1,
            0,
            gl.GL_RGBA,
            gl.GL_UNSIGNED_BYTE,
            white_texture_data,
        )
        gl.glBindTexture(gl.GL_TEXTURE_2D, 0)
        self.renderer_data.texture_slots[0] = self.renderer_data.white_texture

        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, 0)
        gl.glBindVertexArray(0)

    def start_frame(self):
        self.renderer_data.texture_buffer_index = 0

    def end_frame(self):
        assert self.renderer_data.texture_buffer_index is not None
        assert self.renderer_data.texture_buffer is not None

        size = (
            self.renderer_data.texture_buffer_index
            * Vertex((0.0, 0.0), (1.0, 1.0, 1.0, 1.0), (0.0, 0.0), 0.0).data.nbytes
        )

        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.VBO)
        gl.glBufferSubData(
            gl.GL_ARRAY_BUFFER,
            0,
            size,
            self.renderer_data.texture_buffer,
        )

        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)

    def draw_sprite(
        self,
        texture: ArepyTexture,
        src_rect: Optional[tuple[float, float, float, float]] = None,
        src_dest: Optional[tuple[float, float, float, float]] = None,
        color: tuple[int, int, int, int] = (255, 255, 255, 255),
    ):
        """Draw a texture to the screen.

        Args:
            texture (ArepyTexture): The texture to draw.
            src_rect (tuple[w, h, x, y], optional): The source rectangle to draw from the texture.
            src_dest (tuple[w, h, x, y], optional): The destination rectangle to draw to the screen.
            color (tuple[r, g, b, a]): The color of the texture.
        """
        position = src_dest[2:] if src_dest is not None else (0.0, 0.0)
        size = src_rect[:2] if src_rect is not None else texture.get_size()

        if is_outside_screen(position, size, self.get_screen_size()):
            return
        texture_coords = get_texture_coordinates(
            src_rect if src_rect is not None else (0, 0, *texture.get_size()),
            src_dest if src_dest is not None else (0, 0, *texture.get_size()),
        )
        self.submit_texture(texture, position, size, color, texture_coords)

    def submit_texture(
        self,
        texture: ArepyTexture,
        position: tuple[float, float],
        size: tuple[float, float],
        color: tuple[float, float, float, float],
        coords: Optional[
            tuple[float, float, float, float, float, float, float, float]
        ] = None,
    ):
        assert self.renderer_data.texture_buffer_index is not None
        assert self.renderer_data.texture_buffer is not None
        if self.renderer_data.index_count >= self.MAX_INDEX_COUNT or (
            self.renderer_data.texture_slot_index >= self.MAX_TEXTURE_SLOTS - 1
        ):
            self.end_frame()
            self.flush()
            self.start_frame()

        x, y = position
        width, height = size

        # Normalize the position
        screen_width, screen_height = self.get_screen_size()

        gl_x = 2 * x / screen_width - 1
        gl_y = 1 - 2 * y / screen_height
        gl_width = 2 * width / screen_width
        gl_height = 2 * height / screen_height

        texture_slot = self.get_texture_slot(texture.texture_id)

        color = (color[0] / 255, color[1] / 255, color[2] / 255, color[3] / 255)
        coords = coords if coords is not None else DEFAULT_TEXTURE_COORDS

        self.renderer_data.texture_buffer[self.renderer_data.texture_buffer_index] = (
            Vertex((gl_x, gl_y), color, (coords[0], coords[1]), texture_slot).data
        )
        self.renderer_data.texture_buffer[
            self.renderer_data.texture_buffer_index + 1
        ] = Vertex(
            (gl_x + gl_width, gl_y),
            color,
            (coords[2], coords[3]),
            texture_slot,
        ).data
        self.renderer_data.texture_buffer[
            self.renderer_data.texture_buffer_index + 2
        ] = Vertex(
            (gl_x + gl_width, gl_y - gl_height),
            color,
            (coords[4], coords[5]),
            texture_slot,
        ).data
        self.renderer_data.texture_buffer[
            self.renderer_data.texture_buffer_index + 3
        ] = Vertex(
            (gl_x, gl_y - gl_height), color, (coords[6], coords[7]), texture_slot
        ).data
        self.renderer_data.texture_buffer_index += 4
        self.renderer_data.index_count += 6

    def get_texture_slot(self, texture_id):
        if texture_id in self.renderer_data.texture_slots:
            return self.renderer_data.texture_slots.index(texture_id)

        texture_slot = self.renderer_data.texture_slot_index
        self.renderer_data.texture_slots[texture_slot] = texture_id
        self.renderer_data.texture_slot_index += 1
        return texture_slot

    def flush(self):
        # assert self.renderer_data.texture_buffer_index is not None
        gl.glUseProgram(self.shader_program)
        gl.glBindVertexArray(self.VAO)
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.IBO)
        gl.glEnableVertexAttribArray(0)
        gl.glEnableVertexAttribArray(1)
        gl.glEnableVertexAttribArray(2)
        gl.glEnableVertexAttribArray(3)

        _ = [
            gl.glBindTextureUnit(i, self.renderer_data.texture_slots[i])
            for i in range(self.renderer_data.texture_slot_index)
        ]

        gl.glUniformMatrix4fv(
            self.model_location,
            1,
            gl.GL_FALSE,
            MODEL,
        )

        gl.glDrawElementsInstanced(
            gl.GL_TRIANGLES,
            self.renderer_data.index_count,
            gl.GL_UNSIGNED_INT,
            None,
            1,
        )

        gl.glBindTexture(gl.GL_TEXTURE_2D, 0)
        gl.glDisableVertexArrayAttrib(self.VAO, 0)
        gl.glDisableVertexArrayAttrib(self.VAO, 1)
        gl.glDisableVertexArrayAttrib(self.VAO, 2)
        gl.glDisableVertexArrayAttrib(self.VAO, 3)
        gl.glBindVertexArray(0)
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, 0)
        gl.glUseProgram(0)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
        self.renderer_data.index_count = 0

    def draw_rect(
        self, x: int, y: int, width: int, height: int, color: tuple[int, int, int, int]
    ):
        """Draw a rectangle to the screen.

        Args:
            x (int): The x position of the rectangle.
            y (int): The y position of the rectangle.
            width (int): The width of the rectangle.
            height (int): The height of the rectangle.
            color (tuple[int, int, int, int]): The color of the rectangle.
        """

        screen_width, screen_height = self.get_screen_size()

        gl_x = 2 * x / screen_width - 1
        gl_y = 1 - 2 * y / screen_height
        gl_width = 2 * width / screen_width
        gl_height = 2 * height / screen_height

        gl.glBegin(gl.GL_LINE_LOOP)
        gl.glColor4f(*color)
        gl.glVertex2f(gl_x, gl_y)
        gl.glVertex2f(gl_x + gl_width, gl_y)
        gl.glVertex2f(gl_x + gl_width, gl_y - gl_height)
        gl.glVertex2f(gl_x, gl_y - gl_height)
        gl.glEnd()

    def draw_circle(
        self, x: int, y: int, radius: int, color: tuple[int, int, int, int]
    ):
        """Draw a circle to the screen.

        Args:
            x (int): The x position of the circle.
            y (int): The y position of the circle.
            radius (int): The radius of the circle.
            color (tuple[int, int, int, int]): The color of the circle.
        """
        window_width, window_height = self.get_window_size()

        gl_x = 2 * (x + (radius / 2)) / window_width - 1
        gl_y = 1 - 2 * (y + (radius / 2)) / window_height

        radius_width_ratio = radius / window_width
        radius_height_ratio = radius / window_height

        gl.glBegin(gl.GL_LINE_LOOP)
        gl.glColor4f(*color)
        for angle in np.linspace(0, 2 * np.pi, 100):
            gl.glVertex2f(
                gl_x + radius_width_ratio * np.cos(angle),
                gl_y + radius_height_ratio * np.sin(angle),
            )
        gl.glEnd()

    def draw_line(
        self,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        color: tuple[int, int, int, int],
        size: int = 1,
    ):
        """Draw a line to the screen.

        Args:
            x1 (int): The x position of the start of the line.
            y1 (int): The y position of the start of the line.
            x2 (int): The x position of the end of the line.
            y2 (int): The y position of the end of the line.
            color (tuple[int, int, int, int]): The color of the line.
        """
        window_width, window_height = self.get_window_size()

        # opengl +4

        gl_x1 = 2 * x1 / window_width - 1
        gl_y1 = 1 - 2 * y1 / window_height

        gl_x2 = 2 * x2 / window_width - 1
        gl_y2 = 1 - 2 * y2 / window_height

        gl.glLineWidth(size)
        gl.glBegin(gl.GL_LINES)
        gl.glColor4f(*color)
        gl.glVertex2f(gl_x1, gl_y1)
        gl.glVertex2f(gl_x2, gl_y2)
        gl.glEnd()

    def create_texture(self, path: str) -> ArepyTexture:
        """Create a texture from a file.

        Args:
            path (str): The path to the file.

        Returns:
            ArepyTexture: The texture.
        """
        image = Image.open(path)
        image_data = image.tobytes("raw", "RGBA", 0, -1)

        width, height = image.size
        image.close()
        texture = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, texture)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_REPEAT)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_REPEAT)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)

        gl.glTexImage2D(
            gl.GL_TEXTURE_2D,
            0,
            gl.GL_RGBA,
            width,
            height,
            0,
            gl.GL_RGBA,
            gl.GL_UNSIGNED_BYTE,
            image_data,
        )
        gl.glGenerateMipmap(gl.GL_TEXTURE_2D)
        gl.glBindTexture(gl.GL_TEXTURE_2D, 0)

        return ArepyTexture(texture, size=(width, height))

    def remove_texture(self, texture: ArepyTexture):
        """Remove a texture.

        Args:
            texture (ArepyTexture): The texture to remove.
        """
        gl.glDeleteTextures(texture.texture_id)

    def setup_shader(self):

        self.shader_program: int = compile_default_shader()
        self.model_location = gl.glGetUniformLocation(self.shader_program, "model")
        self.texture_location = gl.glGetUniformLocation(self.shader_program, "textures")
        gl.glUseProgram(self.shader_program)
        samplers = [i for i in range(self.MAX_TEXTURE_SLOTS)]
        gl.glUniform1iv(self.texture_location, self.MAX_TEXTURE_SLOTS, samplers)

        gl.glClearColor(0.1, 0.1, 0.1, 1.0)
        gl.glUseProgram(0)

        return self.shader_program

    def clear(self):
        """Clear the screen."""
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

    def set_window_size(self, new_size: tuple[int, int]):
        window_width, window_height = new_size
        super().set_window_size(new_size)
        gl.glViewport(0, 0, window_width, window_height)

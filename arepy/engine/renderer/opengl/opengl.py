from ctypes import c_uint32
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import OpenGL.GL as gl
from PIL import Image

from .. import ArepyTexture, BaseRenderer
from .shaders import compile_default_shader
from .utils import is_outside_screen


class Vertex:
    def __init__(
        self,
        position: tuple[float, float],
        texture_coords: tuple[float, float],
        text_id: float,
    ):
        self.position = position
        self.texture_coords = texture_coords
        self.text_id = text_id

        self.data = np.array(
            [*self.position, *self.texture_coords, self.text_id], dtype=np.float32
        )


@dataclass
class RendererData:
    index_data: np.ndarray
    index_count: int = field(default=0, init=False)
    t_VBO: Optional[int]
    t_VAO: Optional[int]
    t_IBO: Optional[int]
    t_Buffer: Optional[np.ndarray]
    t_Buffer_ptr: Optional[int]
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
            self.MAX_VERTEX_COUNT * Vertex((0.0, 0.0), (0.0, 0.0), 0.0).data.nbytes,
            None,
            gl.GL_DYNAMIC_DRAW,
        )

        self.VAO = gl.glGenVertexArrays(1)
        gl.glBindVertexArray(self.VAO)
        gl.glEnableVertexAttribArray(0)  # position
        gl.glVertexAttribPointer(0, 2, gl.GL_FLOAT, gl.GL_FALSE, 20, None)
        gl.glEnableVertexAttribArray(1)  # texture coords
        gl.glVertexAttribPointer(
            1, 2, gl.GL_FLOAT, gl.GL_FALSE, 20, gl.ctypes.c_void_p(8)
        )
        gl.glEnableVertexAttribArray(2)  # text id
        gl.glVertexAttribPointer(
            2, 1, gl.GL_FLOAT, gl.GL_FALSE, 20, gl.ctypes.c_void_p(16)
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
            t_VBO=self.VBO,
            t_VAO=self.VAO,
            t_IBO=self.IBO,
            t_Buffer_ptr=0,
            index_data=indices,
            t_Buffer=np.array(
                [Vertex((0.0, 0.0), (0.0, 0.0), 0.0).data] * self.MAX_VERTEX_COUNT,
                dtype=np.float32,
            ),
        )
        assert self.renderer_data.t_Buffer is not None

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

    def setup_vao(self, vbo):
        vao = gl.glGenVertexArrays(1)
        gl.glBindVertexArray(vao)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vbo)
        gl.glEnableVertexAttribArray(0)
        # Position
        gl.glVertexAttribPointer(0, 2, gl.GL_FLOAT, gl.GL_FALSE, 20, None)
        gl.glEnableVertexAttribArray(1)
        # Texture coords
        gl.glVertexAttribPointer(
            1, 2, gl.GL_FLOAT, gl.GL_FALSE, 20, gl.ctypes.c_void_p(8)
        )
        # TextureId
        gl.glEnableVertexAttribArray(2)
        gl.glVertexAttribPointer(
            2, 1, gl.GL_FLOAT, gl.GL_FALSE, 20, gl.ctypes.c_void_p(16)
        )

        gl.glBindVertexArray(0)

        return vao

    def start_frame(self):
        self.renderer_data.t_Buffer_ptr = 0

    def end_frame(self):
        assert self.renderer_data.t_Buffer_ptr is not None
        assert self.renderer_data.t_Buffer is not None

        # size = 80000
        size = (
            self.renderer_data.t_Buffer_ptr
            * Vertex((0.0, 0.0), (0.0, 0.0), 0.0).data.nbytes
        )
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.VBO)
        gl.glBufferSubData(
            gl.GL_ARRAY_BUFFER,
            0,
            size,
            self.renderer_data.t_Buffer,
        )

        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)

    def draw_sprite(
        self,
        texture: ArepyTexture,
        position: tuple[int, int],
        size: tuple[int, int],
        color: tuple[int, int, int, int],
    ):
        """Draw a texture to the screen.

        Args:
            texture (ArepyTexture): The texture to draw.
            position (tuple[int, int]): The position to draw the texture.
            size (tuple[int, int]): The size to draw the texture.
            color (tuple[int, int, int, int]): The color of the texture.
        """
        if is_outside_screen(position, size, self.get_window_size()):
            return
        self.submit_texture(texture, position, size, color)

    def submit_texture(
        self,
        texture: ArepyTexture,
        position: tuple[int, int],
        size: tuple[int, int],
        color: tuple[int, int, int, int],
    ):
        assert self.renderer_data.t_Buffer_ptr is not None
        assert self.renderer_data.t_Buffer is not None
        if self.renderer_data.index_count >= self.MAX_INDEX_COUNT or (
            self.renderer_data.texture_slot_index >= self.MAX_TEXTURE_SLOTS - 1
        ):
            self.end_frame()
            self.flush()
            self.start_frame()

        x, y = position
        width, height = size

        gl_x = 2 * x / self._window_size[0] - 1
        gl_y = 1 - 2 * y / self._window_size[1]
        gl_width = 2 * width / self._window_size[0]
        gl_height = 2 * height / self._window_size[1]

        texture_slot = self.get_texture_slot(texture.texture_id)
        """
                    indices[i + 0] = offset + 0
            indices[i + 1] = offset + 1
            indices[i + 2] = offset + 2

            indices[i + 3] = offset + 0
            indices[i + 4] = offset + 2
            indices[i + 5] = offset + 3
            glTriangles
        
        """
        #    text_coords = [
        #        src_x / tex_width,
        #        src_y / tex_height,
        #        (src_x + src_w) / tex_width,
        #        src_y / tex_height,
        #        src_x / tex_width,
        #        (src_y + src_h) / tex_height,
        #        (src_x + src_w) / tex_width,
        #        (src_y + src_h) / tex_height,
        #    ]

        self.renderer_data.t_Buffer[self.renderer_data.t_Buffer_ptr] = Vertex(
            (gl_x, gl_y), (0.0, 1.0), texture_slot
        ).data
        self.renderer_data.t_Buffer[self.renderer_data.t_Buffer_ptr + 1] = Vertex(
            (gl_x + gl_width, gl_y), (1.0, 1.0), texture_slot
        ).data
        self.renderer_data.t_Buffer[self.renderer_data.t_Buffer_ptr + 2] = Vertex(
            (gl_x + gl_width, gl_y - gl_height), (1.0, 0.0), texture_slot
        ).data
        self.renderer_data.t_Buffer[self.renderer_data.t_Buffer_ptr + 3] = Vertex(
            (gl_x, gl_y - gl_height), (0.0, 0.0), texture_slot
        ).data
        self.renderer_data.t_Buffer_ptr += 4
        self.renderer_data.index_count += 6

    def get_texture_slot(self, texture_id):
        if texture_id in self.renderer_data.texture_slots:
            return self.renderer_data.texture_slots.index(texture_id)

        texture_slot = self.renderer_data.texture_slot_index
        self.renderer_data.texture_slots[texture_slot] = texture_id
        self.renderer_data.texture_slot_index += 1
        return texture_slot

    def flush(self):
        assert self.renderer_data.t_Buffer_ptr is not None

        gl.glUseProgram(self.shader_program)
        gl.glBindVertexArray(self.VAO)
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.IBO)
        gl.glEnableVertexAttribArray(0)
        gl.glEnableVertexAttribArray(1)
        gl.glEnableVertexAttribArray(2)

        for i in range(self.renderer_data.texture_slot_index):
            gl.glBindTextureUnit(i, self.renderer_data.texture_slots[i])

        gl.glUniformMatrix4fv(
            self.model_location,
            1,
            gl.GL_FALSE,
            np.array(
                [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1], dtype=np.float32
            ),
        )

        gl.glDrawElements(
            gl.GL_TRIANGLES,
            self.renderer_data.index_count,
            gl.GL_UNSIGNED_INT,
            None,
        )

        gl.glBindTexture(gl.GL_TEXTURE_2D, 0)
        gl.glDisableVertexArrayAttrib(self.VAO, 0)
        gl.glDisableVertexArrayAttrib(self.VAO, 1)
        gl.glDisableVertexArrayAttrib(self.VAO, 2)
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

        window_width, window_height = self.get_window_size()

        gl_x = 2 * x / window_width - 1
        gl_y = 1 - 2 * y / window_height
        gl_width = 2 * width / window_width
        gl_height = 2 * height / window_height

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
        self, x1: int, y1: int, x2: int, y2: int, color: tuple[int, int, int, int]
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

        gl_x1 = 2 * x1 / window_width - 1
        gl_y1 = 1 - 2 * y1 / window_height
        gl_x2 = 2 * x2 / window_width - 1
        gl_y2 = 1 - 2 * y2 / window_height

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

        self.texture_offset_location = gl.glGetUniformLocation(
            self.shader_program, "textOffset"
        )
        self.texture_scale_location = gl.glGetUniformLocation(
            self.shader_program, "textScale"
        )
        self.texture_color_location = gl.glGetUniformLocation(
            self.shader_program, "ourColor"
        )
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

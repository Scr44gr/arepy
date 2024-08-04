# enable_renderdoc()
import time
from ctypes import c_void_p

import glm
import numpy as np
import OpenGL.GL as gl
from PIL import Image

from .. import ArepyTexture, BaseRenderer, Color, Rect
from .shaders import compile_default_shader
from .utils import enable_renderdoc  # type: ignore
from .utils import (
    RendererData,
    is_outside_screen,
    set_vertex_data,
    update_vertex_transforms,
)

enable_renderdoc()


def onDebugMessage(*args, **kwargs):
    print("args = {0}, kwargs = {1}".format(args, kwargs))


class Vertex:
    def __init__(
        self,
        angle: float,
        position: tuple[float, float],
        color: tuple[float, float, float, float],
        src_rect: tuple[float, float, float, float],
        src_dest: tuple[float, float, float, float],
        texture_size: tuple[float, float],
        texture_id: float,
    ):
        self.angle = angle
        self.position = position
        self.color = color
        self.src_rect = src_rect
        self.src_dest = src_dest
        self.texture_id = texture_id
        self.texture_size = texture_size

        self.data = np.array(
            [
                *self.position,
                *self.color,
                *self.src_rect,
                *self.src_dest,
                *self.texture_size,
                self.texture_id,
                self.angle,
            ],
            dtype=np.float32,
        )


VERTEX = Vertex(
    0.0,
    (0.0, 0.0),
    (1.0, 1.0, 1.0, 1.0),
    (0.0, 0.0, 0.0, 0.0),
    (0.0, 0.0, 0.0, 0.0),
    (0.0, 0.0),
    0.0,
)
VERTEX_SIZE = VERTEX.data.nbytes
print(VERTEX_SIZE)


class OpenGLRenderer(BaseRenderer):

    MAX_QUADS = 20000
    MAX_VERTEX_COUNT = MAX_QUADS * 4
    MAX_INDEX_COUNT = MAX_QUADS * 6
    MAX_TEXTURE_SLOTS = 32

    def __init__(self, screen_size: tuple[int, int], window_size: tuple[int, int]):
        super().__init__(screen_size, window_size)

        self.gl_init()
        self.to_be_transformed_data: list = []
        self._is_transformed = False

    def gl_init(self):
        self.VBO = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.VBO)

        gl.glBufferData(
            gl.GL_ARRAY_BUFFER,
            self.MAX_VERTEX_COUNT * VERTEX.data.nbytes,
            None,
            gl.GL_STREAM_DRAW,
        )

        self.VAO = gl.glGenVertexArrays(1)
        gl.glBindVertexArray(self.VAO)
        gl.glEnableVertexAttribArray(0)  # position is vec2
        stride = VERTEX.data.nbytes
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
        # Src_rect is 4 floats
        gl.glEnableVertexAttribArray(2)
        gl.glVertexAttribPointer(
            2,
            4,
            gl.GL_FLOAT,
            gl.GL_FALSE,
            stride,
            gl.ctypes.c_void_p(6 * 4),
        )
        # Src_dest is 4 floats
        gl.glEnableVertexAttribArray(3)
        gl.glVertexAttribPointer(
            3,
            4,
            gl.GL_FLOAT,
            gl.GL_FALSE,
            stride,
            gl.ctypes.c_void_p(10 * 4),
        )
        # texture size is vec2
        gl.glEnableVertexAttribArray(4)
        gl.glVertexAttribPointer(
            4,
            2,
            gl.GL_FLOAT,
            gl.GL_FALSE,
            stride,
            gl.ctypes.c_void_p(14 * 4),
        )

        # Texture id is 1 float
        gl.glEnableVertexAttribArray(5)
        gl.glVertexAttribPointer(
            5,
            1,
            gl.GL_FLOAT,
            gl.GL_FALSE,
            stride,
            gl.ctypes.c_void_p(16 * 4),
        )

        # angle is 1 float
        gl.glEnableVertexAttribArray(6)
        gl.glVertexAttribPointer(
            6,
            1,
            gl.GL_FLOAT,
            gl.GL_FALSE,
            stride,
            gl.ctypes.c_void_p(17 * 4),
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
            texture_vbo=int(self.VBO),
            texture_vao=int(self.VAO),
            texture_ibo=int(self.IBO),
            index_data=indices,
            quads_buffer=np.zeros((self.MAX_VERTEX_COUNT, 18), dtype=np.float32),
            quads_buffer_index=0,
        )
        assert self.renderer_data.quads_buffer is not None

        self.renderer_data.white_texture = int(gl.glGenTextures(1))
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
        gl.glUseProgram(self.shader_program)
        _ = [
            gl.glBindTextureUnit(i, self.renderer_data.texture_slots[i])
            for i in range(self.renderer_data.texture_slot_index)
        ]
        if self._is_transformed:
            return
        self.renderer_data.quads_buffer_index = 0

    def end_frame(self):
        assert self.renderer_data.quads_buffer_index is not None
        assert self.renderer_data.quads_buffer is not None
        size = self.renderer_data.quads_buffer_index * VERTEX_SIZE
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.VBO)
        gl.glBufferSubData(
            gl.GL_ARRAY_BUFFER,
            0,
            size,
            self.renderer_data.quads_buffer,
        )
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)

    def draw_sprite(
        self,
        texture: ArepyTexture,
        src_rect: Rect,
        src_dest: Rect,
        color: Color = Color(255, 255, 255, 255),
        angle: float = 0.0,
    ):
        """Draw a texture to the screen.

        Args:
            texture (ArepyTexture): The texture to draw.
            src_rect (Rect[w, h, x, y], optional): The source rectangle to draw from the texture.
            src_dest (Rect[w, h, x, y], optional): The destination rectangle to draw to the screen.
            color (Color[r, g, b, a]): The color of the texture.
        """
        position = (src_dest.x, src_dest.y) if src_dest is not None else (0, 0)

        # self.submit_texture(texture, position, color, size, src_rect, src_dest, angle)
        self.to_be_transformed_data.append(
            [
                *position,
                *color.normalize(),
                *src_rect.to_tuple(),
                *src_dest.to_tuple(),
                *texture.get_size(),
                self.get_texture_slot(texture.texture_id),
                angle,
            ]
        )

    def make_vertex_transforms(self):
        assert len(self.to_be_transformed_data) >= 0
        self._is_transformed = True
        set_vertex_data(
            np.array(self.to_be_transformed_data, dtype=np.float32, copy=False),
            self.renderer_data,
        )
        self.to_be_transformed_data.clear()

    def update_vertex_transforms(self):
        assert len(self.to_be_transformed_data) >= 0
        update_vertex_transforms(
            np.array(self.to_be_transformed_data, dtype=np.float32, copy=False),
            self.renderer_data,
        )
        self.to_be_transformed_data.clear()

    def get_texture_slot(self, texture_id):
        if texture_id in self.renderer_data.texture_slots:
            return self.renderer_data.texture_slots.index(texture_id)

        texture_slot = self.renderer_data.texture_slot_index
        self.renderer_data.texture_slots[texture_slot] = texture_id
        self.renderer_data.texture_slot_index += 1
        return texture_slot

    def flush(self):

        if self.renderer_data.quads_buffer_index:
            self.__flush_quads()

    def draw_rect(
        self,
        src_rect: Rect,
        color: Color,
        angle: float = 0.0,
    ):
        """Draw a rectangle to the screen.

        Args:
            src_rect (Rect[width, height, x, y]): The source rectangle.
            color (Color[int, int, int, int]): The color of the rectangle.
        """
        texture = ArepyTexture(
            self.renderer_data.white_texture, size=(src_rect.width, src_rect.height)
        )
        self.draw_sprite(texture, src_rect, src_rect, color, angle)

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
        self.texture_location = gl.glGetUniformLocation(self.shader_program, "textures")
        self.view_location = gl.glGetUniformLocation(self.shader_program, "u_view")
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

    def __flush_quads(self):
        gl.glBindVertexArray(self.VAO)
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.IBO)
        gl.glUseProgram(self.shader_program)

        gl.glDrawElements(
            gl.GL_TRIANGLES,
            self.renderer_data.index_count,
            gl.GL_UNSIGNED_INT,
            None,
            c_void_p(0),
        )
        if self._is_transformed:
            return
        self.renderer_data.index_count = 0

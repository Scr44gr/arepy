Implementar el uso de hilos en tareas de renderizado en OpenGL puede ser complicado debido a las restricciones de la mayoría de las APIs de gráficos, que típicamente requieren que todas las llamadas OpenGL se hagan en el mismo hilo (el hilo del contexto de OpenGL). Sin embargo, la preparación de datos que no involucre directamente llamadas a OpenGL puede ser paralelizada efectivamente usando múltiples hilos. Esto puede incluir calcular transformaciones, ordenar o agrupar objetos basados en sus propiedades, o preparar los datos antes de enviarlos al GPU.

A continuación, te muestro un ejemplo de cómo podrías implementar un sistema básico de multihilos para la preparación de datos antes de su envío a OpenGL, utilizando la biblioteca `concurrent.futures` en Python:

```python
import concurrent.futures
import numpy as np

class OpenGLRenderer(BaseRenderer):
    # Supongamos que tienes ya definidas todas las demás propiedades y métodos necesarios
    
    def prepare_sprite_data(self, sprites):
        """Prepara los datos de varios sprites para ser renderizados."""
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Preparar los datos de cada sprite en hilos separados
            futures = [executor.submit(self.calculate_sprite_data, sprite) for sprite in sprites]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        return results

    def calculate_sprite_data(self, sprite):
        """Calcula los datos necesarios para un sprite. Esta función simula la preparación de los datos."""
        # Simula algún tipo de cálculo para preparar los datos del sprite
        texture_slot = self.get_texture_slot(sprite.texture.texture_id) # Esto necesita ser thread safe
        transform_data = self.calculate_transform(sprite)
        
        return (sprite, transform_data, texture_slot)

    def calculate_transform(self, sprite):
        """Calcula la transformación necesaria para el sprite."""
        # Esta es una simplificación, aquí irían los cálculos matemáticos, por ejemplo, escala, rotación, etc.
        return np.identity(4)  # Matriz de identidad como placeholder
    
    def render_sprites(self, sprites):
        """Renderiza los sprites."""
        prepared_data = self.prepare_sprite_data(sprites)
        
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.VBO)
        for data in prepared_data:
            sprite, transform, texture_slot = data
            # Aquí deberías usar tu método existing para configurar los datos del buffer, etc.
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
        
        # Aquí harías tu llamada de renderizado
```

### Puntos Clave:
- **Hilos y OpenGL**: No realices llamadas a OpenGL fuera del hilo principal dedicado a esto, para evitar problemas de sincronización y errores de ejecución.
- **Thread Safe**: El ejemplo asume que `get_texture_slot` es seguro para hilos, lo cual no es típico. Puedes necesitar mecanismos adicionales como locks o colas de trabajo si algunos recursos tienen que ser compartidos entre hilos.
- **Complejidad Reducida en el Hilo Principal**: Al mover la lógica de preparación de datos a otros hilos, el hilo principal puede centrarse en interacciones rápidas y directas con OpenGL.
- **Decisión de Diseño**: Asegúrate de que cualquier función que afecte el estado de OpenGL se llame desde el hilo apropiado y considera que la multi-threading introduce complejidad y potencial para bugs de difícil detección.

Esta es una introducción básica al uso de multihilos en la preparación de datos para renderizado con OpenGL y deberías adaptar y expandir sobre esta idea basado en tus necesidades específicas y la estructura de tu motor de renderizado.




import concurrent.futures
import time
from dataclasses import dataclass, field
from threading import Lock, Thread
from typing import Optional

import glm
import numpy as np
import OpenGL.GL as gl
import OpenGL_accelerate as gl_accelerate
from PIL import Image

from .. import ArepyTexture, BaseRenderer, Color, Rect
from .shaders import compile_default_quad_shader
from .utils import (CircleVertexData, QuadVertexData, enable_renderdoc,
                    is_outside_screen)

enable_renderdoc()

QUAD_VERTEX_DATA = QuadVertexData(
    0.0,
    (0.0, 0.0),
    (1.0, 1.0, 1.0, 1.0),
    (0.0, 0.0, 0.0, 0.0),
    (0.0, 0.0, 0.0, 0.0),
    (0.0, 0.0),
    0.0,
)

CIRCLE_VERTEX_DATA = CircleVertexData(
    position=(0.0, 0.0),
    color=(1.0, 1.0, 1.0, 1.0),
    radius=0.0,
    thickness=0.0,
    fade=0.0,
)


@dataclass
class RendererData:
    index_data: np.ndarray
    index_count: int = field(default=0, init=False)
    quad_vbo: Optional[int]
    quad_vao: Optional[int]
    quad_ibo: Optional[int]
    quad_buffer: Optional[np.ndarray]
    quad_buffer_index: Optional[int]
    quad_shader: Optional[int]
    quad_vertex_positions: list[glm.vec4] = field(
        default_factory=lambda: [
            glm.vec4(-0.5, 0.5, 0.0, 1.0),
            glm.vec4(0.5, 0.5, 0.0, 1.0),
            glm.vec4(0.5, -0.5, 0.0, 1.0),
            glm.vec4(-0.5, -0.5, 0.0, 1.0),
        ],
        init=False,
    )
    # Circle buffer
    circle_buffer: Optional[np.ndarray] = field(default=None, init=False)
    circle_buffer_index: Optional[int] = field(default=0, init=False)
    circle_shader: Optional[int] = field(default=None, init=False)
    circle_vao: Optional[int] = field(default=None, init=False)
    circle_vbo: Optional[int] = field(default=None, init=False)

    # Textures
    white_texture: int = field(default=0, init=False)
    white_texture_slot: int = field(default=0, init=False)
    texture_slots: list[int] = field(default_factory=lambda: [0] * 32, init=False)
    texture_slot_index: int = field(default=1, init=False)


class OpenGLRenderer(BaseRenderer):
    MAX_TRIANGLES = 5000
    MAX_VERTEX_COUNT = MAX_TRIANGLES * 4
    MAX_INDEX_COUNT = MAX_TRIANGLES * 6
    MAX_TEXTURE_SLOTS = 32

    def __init__(self, screen_size: tuple[int, int], window_size: tuple[int, int]):
        super().__init__(screen_size, window_size)
        self.sprites_data = []
        self.gl_init()

    def gl_init(self):
        self.VBO = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.VBO)
        self.VAO = self.create_quad_vertex_array()
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
            indices.nbytes,
            indices,
            gl.GL_STATIC_DRAW,
        )

        self.setup_quad_shader()

        # Enable blending
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

        self.renderer_data = RendererData(
            quad_vbo=self.VBO,
            quad_vao=self.VAO,
            quad_ibo=self.IBO,
            quad_buffer_index=0,
            index_data=indices,
            quad_buffer=np.array(
                [QUAD_VERTEX_DATA.data] * self.MAX_VERTEX_COUNT,
                dtype=np.float32,
            ),
            quad_shader=self.quad_shader,
        )
        self.renderer_data.circle_vao, self.renderer_data.circle_vbo = (
            self.create_circle_vertex_array()
        )

        assert self.renderer_data.quad_buffer is not None

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

    def create_quad_vertex_array(self):
        VAO = gl.glGenVertexArrays(1)
        gl.glBindVertexArray(VAO)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.VBO)
        gl.glBufferData(
            gl.GL_ARRAY_BUFFER,
            self.MAX_VERTEX_COUNT * QUAD_VERTEX_DATA.data.nbytes,
            None,
            gl.GL_DYNAMIC_DRAW,
        )

        stride = QUAD_VERTEX_DATA.data.nbytes
        gl.glEnableVertexAttribArray(0)  # position is vec2
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
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
        gl.glBindVertexArray(0)

        return VAO

    def create_circle_vertex_array(self):
        VBO = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, VBO)
        gl.glBufferData(
            gl.GL_ARRAY_BUFFER,
            self.MAX_VERTEX_COUNT * CIRCLE_VERTEX_DATA.data.nbytes,
            None,
            gl.GL_DYNAMIC_DRAW,
        )

        VAO = gl.glGenVertexArrays(1)
        gl.glBindVertexArray(VAO)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, VBO)
        gl.glBufferData(
            gl.GL_ARRAY_BUFFER,
            self.MAX_VERTEX_COUNT * CIRCLE_VERTEX_DATA.data.nbytes,
            None,
            gl.GL_DYNAMIC_DRAW,
        )
        stride = CIRCLE_VERTEX_DATA.data.nbytes
        gl.glEnableVertexAttribArray(0)
        gl.glVertexAttribPointer(
            0,
            2,
            gl.GL_FLOAT,
            gl.GL_FALSE,
            stride,
            gl.ctypes.c_void_p(0),
        )  # position is vec2
        gl.glEnableVertexAttribArray(1)
        gl.glVertexAttribPointer(
            1,
            4,
            gl.GL_FLOAT,
            gl.GL_FALSE,
            stride,
            gl.ctypes.c_void_p(2 * 4),
        )  # color is 4 floats
        gl.glEnableVertexAttribArray(2)
        gl.glVertexAttribPointer(
            2,
            1,
            gl.GL_FLOAT,
            gl.GL_FALSE,
            stride,
            gl.ctypes.c_void_p(6 * 4),
        )  # radius is 1 float
        gl.glEnableVertexAttribArray(3)
        gl.glVertexAttribPointer(
            3,
            1,
            gl.GL_FLOAT,
            gl.GL_FALSE,
            stride,
            gl.ctypes.c_void_p(7 * 4),
        )  # thickness is 1 float
        gl.glEnableVertexAttribArray(4)
        gl.glVertexAttribPointer(
            4,
            1,
            gl.GL_FLOAT,
            gl.GL_FALSE,
            stride,
            gl.ctypes.c_void_p(8 * 4),
        )  # fade is 1 float

        gl.glBindVertexArray(0)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
        gl.glBindVertexArray(0)

        return VAO, VBO

    def start_frame(self):
        # BIND vao
        gl.glUseProgram(self.quad_shader)

        self.renderer_data.quad_buffer_index = 0

    def end_frame(self):
        assert self.renderer_data.quad_buffer_index is not None
        assert self.renderer_data.quad_buffer is not None


        # Bind the VBO
        size = self.renderer_data.quad_buffer_index * QUAD_VERTEX_DATA.data.nbytes
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.VBO)
        gl.glBufferSubData(
            gl.GL_ARRAY_BUFFER,
            0,
            size,
            self.renderer_data.quad_buffer.size,
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
        size = (
            (src_rect.width, src_rect.height)
            if src_rect is not None
            else texture.get_size()
        )
        if is_outside_screen(position, size, self.get_screen_size()):
            return

        self.sprites_data.append(
            (texture, position, color, size, src_rect, src_dest, angle)
        )

    def get_vertex_data(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [
                executor.submit(self.calculate_vertex_transforms, *args)
                for args in self.sprites_data
            ]
            results = [
                future.result() for future in concurrent.futures.as_completed(futures)
            ]
        return results

    def calculate_vertex_transforms(
        self,
        texture: ArepyTexture,
        position: tuple[float, float],
        color: Color,
        size: tuple[float, float],
        src_rect: Rect,
        dest_rect: Rect,
        angle: float = 1.0,
    ):
        x, y = position

        screen_width, screen_height = self.get_screen_size()
        x = 2 * x / screen_width - 1
        y = 1 - 2 * y / screen_height

        gl_width = 2 * size[0] / screen_width
        gl_height = 2 * size[1] / screen_height

        texture_slot = self.get_texture_slot(texture.texture_id)
        texture_size = texture.get_size()

        color_data = color.normalize()

        transform = (
            glm.translate(glm.mat4(1.0), glm.vec3(x, y, 0.0))
            * glm.rotate(glm.mat4(1.0), angle, glm.vec3(0.0, 0.0, 1.0))
            * glm.scale(glm.mat4(1.0), glm.vec3(gl_width, gl_height, 1.0))
        )
        src_rect_data = src_rect.to_tuple()
        dest_rect_data = dest_rect.to_tuple()
        result = []
        for i in range(4):
            vertex = QuadVertexData(
                angle,
                position=(
                    transform * self.renderer_data.quad_vertex_positions[i]
                ).to_tuple()[
                    :2
                ],  # Top left vertex
                color=color_data,
                src_rect=src_rect_data,
                src_dest=dest_rect_data,
                texture_size=texture_size,
                texture_id=texture_slot,
            ).data
            result.append(vertex)
        return result

    def submit_vertex_data(self, vertex: QuadVertexData):
        assert self.renderer_data.quad_buffer_index is not None
        assert self.renderer_data.quad_buffer is not None
        if self.renderer_data.index_count >= self.MAX_INDEX_COUNT or (
            self.renderer_data.texture_slot_index >= self.MAX_TEXTURE_SLOTS - 1
        ):
            self.end_frame()
            self.flush()
            self.start_frame()
        self.renderer_data.quad_buffer[self.renderer_data.quad_buffer_index] = vertex
        self.renderer_data.quad_buffer_index += 1

        self.renderer_data.index_count += 6

    def submit_textures(self):
        vertex_result = self.get_vertex_data()

        for vertex in vertex_result:
            for v in vertex:
                self.submit_vertex_data(v)

        self.vertex_data = []

    def get_texture_slot(self, texture_id):
        if texture_id in self.renderer_data.texture_slots:
            return self.renderer_data.texture_slots.index(texture_id)

        texture_slot = self.renderer_data.texture_slot_index
        self.renderer_data.texture_slots[texture_slot] = texture_id
        self.renderer_data.texture_slot_index += 1
        return texture_slot

    def flush(self):

        if self.renderer_data.quad_buffer_index:
            self.__flush_quads()
        if self.renderer_data.circle_buffer_index:
            ...  # TODO: Implement circle drawing

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
        ...

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
        ...

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

    def setup_quad_shader(self):

        self.quad_shader: int = compile_default_quad_shader()
        self.texture_location = gl.glGetUniformLocation(self.quad_shader, "textures")
        self.view_location = gl.glGetUniformLocation(self.quad_shader, "u_view")
        gl.glUseProgram(self.quad_shader)
        samplers = [i for i in range(self.MAX_TEXTURE_SLOTS)]
        gl.glUniform1iv(self.texture_location, self.MAX_TEXTURE_SLOTS, samplers)

        gl.glClearColor(0.1, 0.1, 0.1, 1.0)

        return self.quad_shader

    def clear(self):
        """Clear the screen."""
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

    def set_window_size(self, new_size: tuple[int, int]):
        window_width, window_height = new_size
        super().set_window_size(new_size)
        gl.glViewport(0, 0, window_width, window_height)

    def __flush_quads(self):

        _ = [
            gl.glBindTextureUnit(i, self.renderer_data.texture_slots[i])
            for i in range(self.renderer_data.texture_slot_index)
        ]
        gl.glBindVertexArray(self.VAO)
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.IBO)

        gl.glDrawElements(
            gl.GL_TRIANGLES,
            self.renderer_data.index_count,
            gl.GL_UNSIGNED_INT,
            ctypes.c_void_p(0),
        )
        self.renderer_data.index_count = 0
        self.renderer_data.texture_slot_index = 1


import ctypes

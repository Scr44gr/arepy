import numpy as np
import OpenGL.GL as gl
from PIL import Image

from . import ArepyTexture, BaseRenderer


class OpenGLRenderer(BaseRenderer):
    def __init__(self, screen_size: tuple[int, int], window_size: tuple[int, int]):
        super().__init__(screen_size, window_size)
        self.vertex_data = np.array(
            [
                # positions    # texture coords
                0.5,
                0.5,
                0.0,
                1.0,
                1.0,  # top right
                0.5,
                -0.5,
                0.0,
                1.0,
                0.0,  # bottom right
                -0.5,
                -0.5,
                0.0,
                0.0,
                0.0,  # bottom left
                -0.5,
                0.5,
                0.0,
                0.0,
                1.0,  # top left
            ],
            dtype=np.float32,
        )

        self.VBO = self.setup_vbo()
        self.VBO_2 = self.setup_vbo()
        self.setup_shader()
        self.VAO = self.setup_vao(self.VBO)
        self.VAO_2 = self.setup_vao(self.VBO)

    def setup_vbo(self):
        vbo = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vbo)
        gl.glBufferData(
            gl.GL_ARRAY_BUFFER,
            self.vertex_data.nbytes,
            self.vertex_data,
            gl.GL_DYNAMIC_DRAW,
        )
        return vbo

    def setup_vao(self, vbo):
        vao = gl.glGenVertexArrays(1)
        gl.glBindVertexArray(vao)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vbo)

        gl.glVertexAttribPointer(0, 3, gl.GL_FLOAT, gl.GL_FALSE, 20, None)
        gl.glEnableVertexAttribArray(0)

        gl.glVertexAttribPointer(
            1, 2, gl.GL_FLOAT, gl.GL_FALSE, 20, gl.ctypes.c_void_p(12)
        )

        gl.glEnableVertexAttribArray(1)

        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
        gl.glBindVertexArray(0)

        return vao

    def setup_shader(self):
        self.vertex_shader = """
        #version 330 core
        layout (location = 0) in vec3 aPos;
        layout (location = 1) in vec2 aTexCoord;

        out vec2 TexCoord;
        uniform mat4 transform;
        void main() {
            gl_Position = transform * vec4(aPos, 1.0);
            TexCoord = aTexCoord;
        }
        """
        self.fragment_shader = """
        #version 330 core
        out vec4 FragColor;

        in vec2 TexCoord;

        uniform sampler2D texture1;
        uniform vec2 textOffset;
        uniform vec2 textScale;
        uniform vec4 ourColor = vec4(1.0, 1.0, 1.0, 1.0);

        void main() {
            FragColor = texture(texture1, TexCoord * textScale + textOffset);
            FragColor = FragColor * ourColor;
        }
        """
        self.texture_shader = self.create_shader(
            self.vertex_shader, self.fragment_shader
        )
        self.draw_shader = self.create_shader(self.vertex_shader, self.fragment_shader)
        self.texture_offset_location = gl.glGetUniformLocation(
            self.texture_shader, "textOffset"
        )
        self.texture_scale_location = gl.glGetUniformLocation(
            self.texture_shader, "textScale"
        )
        self.texture_color_location = gl.glGetUniformLocation(
            self.texture_shader, "ourColor"
        )
        self.transform_location = gl.glGetUniformLocation(
            self.texture_shader, "transform"
        )
        self.texture_location = gl.glGetUniformLocation(self.texture_shader, "texture1")

    def clear(self):
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

    def render(
        self,
        texture: ArepyTexture,
        src_rect: tuple[int, int, int, int],
        dest_rect: tuple[int, int, int, int],
    ):
        """Render a texture to the screen.

        Args:
            texture (ArepyTexture): The texture to render.
            src_rect (tuple[int, int, int, int]): The source rect to render from.
            dest_rect (tuple[int, int, int, int]): The destination rect to render to.
        """
        gl.glUseProgram(self.texture_shader)
        gl.glBindVertexArray(self.VAO)

        # Get the texture size
        tex_width, tex_height = texture.get_size()
        src_x, src_y, src_w, src_h = src_rect

        # Calculate the texture offset and scale
        tex_x = src_x / tex_width
        tex_y = src_y / tex_height
        tex_w = src_w / tex_width
        tex_h = src_h / tex_height

        # Pass the texture size to the shader
        gl.glUniform2f(self.texture_offset_location, tex_x, tex_y)
        gl.glUniform2f(self.texture_scale_location, tex_w, tex_h)

        x, y, width, height = dest_rect
        window_width, window_height = self.get_window_size()
        gl_x = 2 * x / window_width - 1
        gl_y = 1 - 2 * y / window_height
        gl_width = 2 * width / window_width
        gl_height = 2 * height / window_height

        model = np.array(
            [
                [gl_width, 0, 0, 0],
                [0, gl_height, 0, 0],
                [0, 0, 1, 0],
                [gl_x, gl_y, 0, 1],
            ],
            dtype=np.float32,
        )

        # Pass the model matrix to the shader
        gl.glUniformMatrix4fv(self.transform_location, 1, gl.GL_FALSE, model)

        # Enable blending
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

        # Bind the texture
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, texture.texture_id)
        gl.glUniform1i(self.texture_location, 0)
        gl.glEnableVertexAttribArray(1)
        gl.glDrawArrays(gl.GL_TRIANGLE_FAN, 0, 4)

        # Unbind the texture
        gl.glBindVertexArray(0)
        gl.glDisable(gl.GL_BLEND)
        gl.glUseProgram(0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, 0)

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

    def create_shader(self, vertex_shader, fragment_shader):
        vertex = gl.glCreateShader(gl.GL_VERTEX_SHADER)
        gl.glShaderSource(vertex, vertex_shader)
        gl.glCompileShader(vertex)
        if not gl.glGetShaderiv(vertex, gl.GL_COMPILE_STATUS):
            raise RuntimeError(gl.glGetShaderInfoLog(vertex))
        fragment = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)
        gl.glShaderSource(fragment, fragment_shader)
        gl.glCompileShader(fragment)
        if not gl.glGetShaderiv(fragment, gl.GL_COMPILE_STATUS):
            raise RuntimeError(gl.glGetShaderInfoLog(fragment))
        shader = gl.glCreateProgram()
        gl.glAttachShader(shader, vertex)
        gl.glAttachShader(shader, fragment)
        gl.glLinkProgram(shader)
        if not gl.glGetProgramiv(shader, gl.GL_LINK_STATUS):
            raise RuntimeError(gl.glGetProgramInfoLog(shader))  # type: ignore
        gl.glDeleteShader(vertex)
        gl.glDeleteShader(fragment)
        return shader

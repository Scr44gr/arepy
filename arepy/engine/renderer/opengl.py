import moderngl
import numpy as np
import OpenGL.GL as gl

from . import BaseRenderer


# pyopengl sdl2
class OpenGLRenderer(BaseRenderer):
    def __init__(self):
        super().__init__()
        self.vertices = np.asarray(
            [
                -1.0,
                -1.0,
                0.0,
                -1.0,
                1.0,
                0.0,
                1.0,
                1.0,
                0.0,
                -1.0,
                -1.0,
                0.0,
                1.0,
                -1.0,
                0.0,
                1.0,
                1.0,
                0.0,
            ],
            np.float32,
        )
        # vertex shader of textures
        self.vertex_shader = """
        #version 330 core
        layout (location = 0) in vec3 aPos;
        layout (location = 1) in vec3 aColor;
        layout (location = 2) in vec2 aTexCoord;
        
        out vec3 ourColor;
        out vec2 TexCoord;
        
        void main()
        {
            gl_Position = vec4(aPos, 1.0);
            ourColor = aColor;
            TexCoord = aTexCoord;
        }
        """
        self.fragment_shader = """
        #version 330 core
        out vec4 FragColor;

        in vec3 ourColor;
        in vec2 TexCoord;

        uniform sampler2D ourTexture;

        void main()
        {
            FragColor = texture(ourTexture, TexCoord);
        }
        """
        # setup moderngl
        self.ctx = moderngl.create_context()
        self.vbo = self.setup_vbo(self.vertices)
        self.shader = self.create_shader(self.vertex_shader, self.fragment_shader)
        self.vao = self.setup_vao(self.vbo, self.shader)

    def setup_vbo(self, vertices):
        vbo = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vbo)
        gl.glBufferData(
            gl.GL_ARRAY_BUFFER, vertices.nbytes, vertices, gl.GL_STATIC_DRAW
        )
        return vbo

    def setup_vao(self, vbo, shader):
        vao = gl.glGenVertexArrays(1)
        gl.glBindVertexArray(vao)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, vbo)
        position = gl.glGetAttribLocation(shader, "aPos")
        gl.glEnableVertexAttribArray(position)

        gl.glVertexAttribPointer(position, 3, gl.GL_FLOAT, gl.GL_FALSE, 0, None)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
        gl.glBindVertexArray(0)
        return vao

    def clear(self):
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

    def render(self, texture):
        self.ctx.clear(1.0, 1.0, 1.0)

    def draw_texture(self, texture_id, x, y, width, height):
        # render texture with moderngl from texture_)id
        texture = self.ctx.texture(
            (width, height), 3, np.frombuffer(texture_id, np.uint8)
        )
        texture.use()
        self.vao.render(moderngl.TRIANGLES)

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
            raise RuntimeError(gl.glGetProgramInfoLog(shader))
        gl.glDeleteShader(vertex)
        gl.glDeleteShader(fragment)
        return shader

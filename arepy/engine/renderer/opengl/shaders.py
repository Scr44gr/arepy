DEFAULT_VERTEX_SHADER = """
#version 330 core
layout (location = 0) in vec2 aPos;
layout (location = 1) in vec2 aTexCoord;
layout (location = 2) in float aTextId;

out vec2 TexCoord;
out float TextIndex;
uniform mat4 model;

void main() {
    gl_Position = model * vec4(aPos, 1.0, 1.0);
    TexCoord = aTexCoord;
    TextIndex = aTextId;
}
"""
DEFAULT_FRAGMENT_SHADER = """
#version 330 core
out vec4 FragColor;

in vec2 TexCoord;
in float TextIndex;

uniform sampler2D textures[32];
uniform vec2 textOffset;
uniform vec2 textScale;
uniform vec4 ourColor = vec4(1.0, 1.0, 1.0, 1.0);


void main() {
    int index = int(TextIndex);
    FragColor = texture(textures[index], TexCoord );
    FragColor = FragColor * ourColor;
    
}
"""
from typing import cast

import OpenGL.GL as gl


def create_shader(vertex_shader: str, fragment_shader: str) -> int:
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
    return cast(int, shader)


def compile_default_shader():
    return create_shader(DEFAULT_VERTEX_SHADER, DEFAULT_FRAGMENT_SHADER)

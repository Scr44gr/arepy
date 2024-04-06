DEFAULT_VERTEX_SHADER = """
// Vertex Shader
#version 330 core
layout (location = 0) in vec2 in_position;  // Vertex position
layout (location = 1) in vec4 in_color;  // Vertex color
layout (location = 2) in vec4 in_srcRect;  // Source rectangle (x=w, y=h, w=x, z=y)
layout (location = 3) in vec4 in_dstRect;  // Destination rectangle (x=w, y=h, w=x, z=y)
layout (location = 4) in vec2 in_texSize; // texture size
layout (location = 5) in float in_textId;  // Texture ID
layout (location = 6) in float in_angle;  // Rotation angle

out vec4 out_color;
out float out_textId;
out vec2 out_texCoord;
out vec2 out_texSize;
out float out_angle;

uniform mat4 u_view = mat4(1.0);
uniform mat4 u_projection = mat4(1.0);
uniform int u_verticesPerPrimitive = 4;

vec2 calculateTextureCoordinates(float x, float y, float w, float h, float texture_width, float texture_height) {
    if (gl_VertexID % u_verticesPerPrimitive == 0) {
        return vec2(x / texture_width, (y + h) / texture_height);
    } else if (gl_VertexID % u_verticesPerPrimitive == 1) {
        return vec2((x + w) / texture_width, (y + h) / texture_height);
    } else if (gl_VertexID % u_verticesPerPrimitive == 2) {
        return vec2((x + w) / texture_width, y / texture_height);
    } else {
        return vec2(x / texture_width, y / texture_height);
    }
}


void main() {
    float texture_width = in_dstRect.x;
    float texture_height = in_dstRect.y;
    float w = in_srcRect.x;
    float h = in_srcRect.y;
    float x = in_srcRect.z;
    float y = in_srcRect.w;
    out_texCoord = calculateTextureCoordinates(x, y, w, h, texture_width, texture_height);

    gl_Position = u_projection * u_view * vec4(in_position, 0.0, 1.0);
    out_textId = in_textId;
    out_color = in_color;
}
"""

DEFAULT_FRAGMENT_SHADER = """
#version 330 core
out vec4 FragColor;

in vec2 out_texCoord;
in float out_textId;
in vec4 out_color;


uniform sampler2D textures[32];

void main() {
    int index = int(out_textId);
    FragColor = texture(textures[index], out_texCoord) * out_color;
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

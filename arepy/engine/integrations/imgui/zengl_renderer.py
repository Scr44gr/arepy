from __future__ import annotations

import struct
from ctypes import CFUNCTYPE, c_byte, c_int, c_ssize_t, c_void_p, cast as c_cast
from typing import Any, cast

import zengl
from OpenGL import GL
from imgui_bundle import imgui
from imgui_bundle.python_backends.opengl_base_backend import (
    BaseOpenGLRenderer,
    get_common_gl_state,
    restore_common_gl_state,
)


class OpenGLBindings:
    GL_TEXTURE0 = 0x84C0
    GL_TEXTURE_2D = 0x0DE1
    GL_ARRAY_BUFFER = 0x8892
    GL_ELEMENT_ARRAY_BUFFER = 0x8893
    GL_STREAM_DRAW = 0x88E0
    GL_TRIANGLES = 0x0004
    GL_UNSIGNED_SHORT = 0x1403
    GL_UNSIGNED_INT = 0x1405
    GL_SCISSOR_TEST = 0x0C11

    def __init__(self, ctx: zengl.Context) -> None:
        loader = cast(Any, ctx.loader).load_opengl_function
        self.glEnable = c_cast(loader("glEnable"), CFUNCTYPE(None, c_int))
        self.glDisable = c_cast(loader("glDisable"), CFUNCTYPE(None, c_int))
        self.glScissor = c_cast(
            loader("glScissor"), CFUNCTYPE(None, c_int, c_int, c_int, c_int)
        )
        self.glActiveTexture = c_cast(loader("glActiveTexture"), CFUNCTYPE(None, c_int))
        self.glBindTexture = c_cast(
            loader("glBindTexture"), CFUNCTYPE(None, c_int, c_int)
        )
        self.glBindBuffer = c_cast(
            loader("glBindBuffer"), CFUNCTYPE(None, c_int, c_int)
        )
        self.glBufferData = c_cast(
            loader("glBufferData"), CFUNCTYPE(None, c_int, c_ssize_t, c_void_p, c_int)
        )
        self.glDrawElementsInstanced = c_cast(
            loader("glDrawElementsInstanced"),
            CFUNCTYPE(None, c_int, c_int, c_int, c_void_p, c_int),
        )


class ZenglRenderer(BaseOpenGLRenderer):
    __slots__ = (
        "ctx",
        "gl",
        "pipeline",
        "vertex_buffer",
        "index_buffer",
        "vertex_buffer_handle",
        "index_buffer_handle",
        "placeholder_texture",
    )

    def __init__(self, ctx: zengl.Context | None = None) -> None:
        self.ctx = ctx or zengl.context()
        self.gl: OpenGLBindings | None = None
        self.pipeline: zengl.Pipeline | None = None
        self.vertex_buffer: zengl.Buffer | None = None
        self.index_buffer: zengl.Buffer | None = None
        self.vertex_buffer_handle = 0
        self.index_buffer_handle = 0
        self.placeholder_texture: zengl.Image | None = None
        super().__init__()

    def _create_device_objects(self) -> None:
        self.vertex_buffer = self.ctx.buffer(size=1)
        self.index_buffer = self.ctx.buffer(size=1, index=True)
        self.placeholder_texture = self.ctx.image(
            (1, 1),
            "rgba8unorm",
            b"\xff\xff\xff\xff",
        )

        version = "#version 330 core"
        if "WebGL" in self.ctx.info["version"] or "OpenGL ES" in self.ctx.info["version"]:
            version = "#version 300 es\nprecision highp float;"

        self.pipeline = self.ctx.pipeline(
            includes={"version": version},
            vertex_shader="""
                #include \"version\"

                uniform vec2 Scale;

                layout (location = 0) in vec2 in_vertex;
                layout (location = 1) in vec2 in_uv;
                layout (location = 2) in vec4 in_color;

                out vec2 v_uv;
                out vec4 v_color;

                void main() {
                    v_uv = in_uv;
                    v_color = in_color;
                    gl_Position = vec4(in_vertex.xy * Scale - 1.0, 0.0, 1.0);
                    gl_Position.y = -gl_Position.y;
                }
            """,
            fragment_shader="""
                #include \"version\"

                uniform sampler2D Texture;

                in vec2 v_uv;
                in vec4 v_color;

                layout (location = 0) out vec4 out_color;

                void main() {
                    out_color = texture(Texture, v_uv) * v_color;
                }
            """,
            layout=[
                {
                    "name": "Texture",
                    "binding": 0,
                },
            ],
            resources=[
                {
                    "type": "sampler",
                    "binding": 0,
                    "image": self.placeholder_texture,
                    "min_filter": "nearest",
                    "mag_filter": "nearest",
                },
            ],
            blend={
                "enable": True,
                "src_color": "src_alpha",
                "dst_color": "one_minus_src_alpha",
            },
            uniforms={
                "Scale": [0.0, 0.0],
            },
            topology="triangles",
            framebuffer=None,
            viewport=(0, 0, 0, 0),
            vertex_buffers=zengl.bind(self.vertex_buffer, "2f 2f 4nu1", 0, 1, 2),
            index_buffer=self.index_buffer,
            instance_count=0,
        )

        self.gl = OpenGLBindings(self.ctx)
        inspect = cast(Any, zengl.inspect)
        self.vertex_buffer_handle = inspect(self.vertex_buffer)["buffer"]
        self.index_buffer_handle = inspect(self.index_buffer)["buffer"]

    def render(self, draw_data: imgui.ImDrawData | None) -> None:
        if self.pipeline is None or self.gl is None:
            return
        self._update_textures()

        if draw_data is None:
            draw_data = imgui.get_draw_data()

        display_width, display_height = self.io.display_size
        fb_width = int(display_width * self.io.display_framebuffer_scale[0])
        fb_height = int(display_height * self.io.display_framebuffer_scale[1])

        if draw_data is None or fb_width == 0 or fb_height == 0:
            return

        draw_data.scale_clip_rects(self.io.display_framebuffer_scale)

        common_gl_state = get_common_gl_state()
        last_program = GL.glGetIntegerv(GL.GL_CURRENT_PROGRAM)
        last_active_texture = GL.glGetIntegerv(GL.GL_ACTIVE_TEXTURE)
        last_array_buffer = GL.glGetIntegerv(GL.GL_ARRAY_BUFFER_BINDING)
        last_element_array_buffer = GL.glGetIntegerv(
            GL.GL_ELEMENT_ARRAY_BUFFER_BINDING
        )
        last_vertex_array = GL.glGetIntegerv(GL.GL_VERTEX_ARRAY_BINDING)

        frame_started = False
        self.ctx.new_frame(clear=False)
        frame_started = True

        try:
            uniforms = self.pipeline.uniforms
            assert uniforms is not None

            self.pipeline.viewport = (0, 0, fb_width, fb_height)
            uniforms["Scale"][:] = struct.pack(
                "2f", 2.0 / display_width, 2.0 / display_height
            )
            self.pipeline.render()

            gl = self.gl
            index_type = (
                gl.GL_UNSIGNED_SHORT if imgui.INDEX_SIZE == 2 else gl.GL_UNSIGNED_INT
            )

            gl.glEnable(gl.GL_SCISSOR_TEST)
            gl.glActiveTexture(gl.GL_TEXTURE0)

            for commands in draw_data.cmd_lists:
                running_index_offset = 0
                vertex_size = commands.vtx_buffer.size() * imgui.VERTEX_SIZE
                index_size = commands.idx_buffer.size() * imgui.INDEX_SIZE
                vertex_data = (c_byte * vertex_size).from_address(
                    commands.vtx_buffer.data_address()
                )
                index_data = (c_byte * index_size).from_address(
                    commands.idx_buffer.data_address()
                )

                gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vertex_buffer_handle)
                gl.glBufferData(
                    gl.GL_ARRAY_BUFFER,
                    vertex_size,
                    c_cast(vertex_data, c_void_p),
                    gl.GL_STREAM_DRAW,
                )

                gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.index_buffer_handle)
                gl.glBufferData(
                    gl.GL_ELEMENT_ARRAY_BUFFER,
                    index_size,
                    c_cast(index_data, c_void_p),
                    gl.GL_STREAM_DRAW,
                )

                for command in commands.cmd_buffer:
                    try:
                        index_offset = command.idx_offset
                    except AttributeError:
                        index_offset = running_index_offset
                    x1, y1, x2, y2 = command.clip_rect
                    clip_x1 = max(int(x1), 0)
                    clip_y1 = max(int(fb_height - y2), 0)
                    clip_x2 = min(int(x2), fb_width)
                    clip_y2 = min(int(fb_height - y1), fb_height)
                    if clip_x2 <= clip_x1 or clip_y2 <= clip_y1:
                        running_index_offset += command.elem_count
                        continue

                    gl.glScissor(
                        clip_x1,
                        clip_y1,
                        clip_x2 - clip_x1,
                        clip_y2 - clip_y1,
                    )

                    try:
                        tex_ref = command.tex_ref
                    except AttributeError:
                        tex_ref = None
                    texture_id = (
                        tex_ref.get_tex_id()
                        if tex_ref is not None
                        else command.get_tex_id()
                    )
                    gl.glBindTexture(gl.GL_TEXTURE_2D, texture_id)
                    gl.glDrawElementsInstanced(
                        gl.GL_TRIANGLES,
                        command.elem_count,
                        index_type,
                        c_void_p(index_offset * imgui.INDEX_SIZE),
                        1,
                    )
                    running_index_offset += command.elem_count
        finally:
            if frame_started:
                self.ctx.end_frame(clean=False, flush=False)
            if hasattr(GL, "glBindSampler"):
                GL.glBindSampler(0, 0)
            restore_common_gl_state(common_gl_state)
            GL.glUseProgram(last_program)
            GL.glActiveTexture(last_active_texture)
            GL.glBindVertexArray(last_vertex_array)
            GL.glBindBuffer(GL.GL_ARRAY_BUFFER, last_array_buffer)
            GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, last_element_array_buffer)

    def _invalidate_device_objects(self) -> None:
        if self.pipeline is not None:
            self.ctx.release(self.pipeline)
        if self.vertex_buffer is not None:
            self.ctx.release(self.vertex_buffer)
        if self.index_buffer is not None:
            self.ctx.release(self.index_buffer)
        if self.placeholder_texture is not None:
            self.ctx.release(self.placeholder_texture)

        self.pipeline = None
        self.vertex_buffer = None
        self.index_buffer = None
        self.placeholder_texture = None
        self.vertex_buffer_handle = 0
        self.index_buffer_handle = 0
        self.gl = None
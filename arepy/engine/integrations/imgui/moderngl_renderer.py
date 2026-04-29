# type: ignore
# @see https://github.com/moderngl/moderngl-window/pull/197/commits/67a30750e595de058cca57d9c3676a772157d194
# thx @highfestiva for the implementation :)
import ctypes

import moderngl
from imgui_bundle import imgui
from imgui_bundle.python_backends.opengl_base_backend import BaseOpenGLRenderer
from OpenGL import GL


class ModernGLRenderer(BaseOpenGLRenderer):
    VERTEX_SHADER_SRC = """
        #version 330
        uniform mat4 ProjMtx;
        in vec2 Position;
        in vec2 UV;
        in vec4 Color;
        out vec2 Frag_UV;
        out vec4 Frag_Color;
        void main() {
            Frag_UV = UV;
            Frag_Color = Color;
            gl_Position = ProjMtx * vec4(Position.xy, 0, 1);
        }
    """
    FRAGMENT_SHADER_SRC = """
        #version 330
        uniform sampler2D Texture;
        in vec2 Frag_UV;
        in vec4 Frag_Color;
        out vec4 Out_Color;
        void main() {
            Out_Color = (Frag_Color * texture(Texture, Frag_UV.st));
        }
    """

    __slots__ = (
        "wnd",
        "ctx",
        "_prog",
        "_fbo",
        "_vertex_buffer",
        "_index_buffer",
        "_vao",
        "_textures",
    )

    def __init__(self, *args, **kwargs):
        self._prog = None
        self._fbo = None
        self._vertex_buffer = None
        self._index_buffer = None
        self._vao = None
        self._textures = {}
        self.wnd = kwargs.get("wnd")
        self.ctx = self.wnd.ctx if self.wnd and self.wnd.ctx else kwargs.get("ctx")

        if not self.ctx:
            raise ValueError("Missing moderngl context")

        assert isinstance(self.ctx, moderngl.Context)

        super().__init__()

        if hasattr(self, "wnd") and self.wnd:
            self.resize(*self.wnd.buffer_size)
        elif "display_size" in kwargs:
            self.io.display_size = kwargs.get("display_size")

    def register_texture(self, texture: moderngl.Texture):
        """Make the imgui renderer aware of the texture"""
        self._textures[texture.glo] = texture

    def remove_texture(self, texture: moderngl.Texture):
        """Remove the texture from the imgui renderer"""
        del self._textures[texture.glo]

    def _create_device_objects(self):
        if self._prog is None:
            self._prog = self.ctx.program(
                vertex_shader=self.VERTEX_SHADER_SRC,
                fragment_shader=self.FRAGMENT_SHADER_SRC,
            )
            self.projMat = self._prog["ProjMtx"]
            self._prog["Texture"].value = 0

        if self._vertex_buffer is None:
            self._vertex_buffer = self.ctx.buffer(reserve=imgui.VERTEX_SIZE * 65536)

        if self._index_buffer is None:
            self._index_buffer = self.ctx.buffer(reserve=imgui.INDEX_SIZE * 65536)

        if self._vao is None:
            self._vao = self.ctx.vertex_array(
                self._prog,
                [(self._vertex_buffer, "2f 2f 4f1", "Position", "UV", "Color")],
                index_buffer=self._index_buffer,
                index_element_size=imgui.INDEX_SIZE,
            )

    def render(self, draw_data: imgui.ImDrawData):
        if not draw_data:
            return

        self._update_textures()

        io = self.io
        display_width, display_height = io.display_size
        fb_width = int(display_width * io.display_framebuffer_scale[0])
        fb_height = int(display_height * io.display_framebuffer_scale[1])

        if fb_width == 0 or fb_height == 0:
            return

        self.projMat.value = (
            2.0 / display_width,
            0.0,
            0.0,
            0.0,
            0.0,
            2.0 / -display_height,
            0.0,
            0.0,
            0.0,
            0.0,
            -1.0,
            0.0,
            -1.0,
            1.0,
            0.0,
            1.0,
        )

        draw_data.scale_clip_rects(io.display_framebuffer_scale)
        self.ctx.enable_only(moderngl.BLEND)
        self.ctx.blend_equation = moderngl.FUNC_ADD
        self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA

        for commands in draw_data.cmd_lists:
            vtx_type = ctypes.c_byte * commands.vtx_buffer.size() * imgui.VERTEX_SIZE
            idx_type = ctypes.c_byte * commands.idx_buffer.size() * imgui.INDEX_SIZE
            vtx_arr = (vtx_type).from_address(commands.vtx_buffer.data_address())
            idx_arr = (idx_type).from_address(commands.idx_buffer.data_address())
            self._vertex_buffer.write(vtx_arr)
            self._index_buffer.write(idx_arr)

            idx_pos = 0
            for command in commands.cmd_buffer:
                texture_id = command.tex_ref.get_tex_id()

                GL.glBindTexture(GL.GL_TEXTURE_2D, texture_id)

                x, y, z, w = command.clip_rect
                self.ctx.scissor = int(x), int(fb_height - w), int(z - x), int(w - y)
                self._vao.render(
                    moderngl.TRIANGLES, vertices=command.elem_count, first=idx_pos
                )
                idx_pos += command.elem_count
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        self.ctx.scissor = None

    def _invalidate_device_objects(self):
        if self._vertex_buffer:
            self._vertex_buffer.release()
        if self._index_buffer:
            self._index_buffer.release()
        if self._vao:
            self._vao.release()
        if self._prog:
            self._prog.release()

        self._prog = None
        self._vertex_buffer = None
        self._index_buffer = None
        self._vao = None

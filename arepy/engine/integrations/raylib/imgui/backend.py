# Based on https://github.com/pthom/imgui_bundle/blob/main/bindings/imgui_bundle/python_backends/glfw_backend.py
from __future__ import absolute_import

from typing import Dict

import moderngl
import raylib as rl
from imgui_bundle import ImVec2, imgui
from imgui_bundle.python_backends import compute_fb_scale
from pyray import ffi
from raylib.defines import GLFW_FOCUSED, GLFW_PRESS, GLFW_RELEASE

from .moderngl_renderer import ModernGLRenderer

GlfwKey = int


@ffi.callback("void(GLFWwindow *, int, int, int, int)")
def keyboard_callback(window, key, scancode, action, mods):
    print("keyboard_callback", window, key, scancode, action, mods)


class ImguiRenderer(ModernGLRenderer):
    key_map: Dict[GlfwKey, imgui.Key]
    modifier_map: Dict[GlfwKey, imgui.Key]

    def __init__(self, attach_callbacks: bool = True):
        super(ImguiRenderer, self).__init__(ctx=moderngl.get_context())
        self.window = rl.glfwGetCurrentContext()

        if attach_callbacks:
            self._keyboard_callback = ffi.callback(
                "void(GLFWwindow *, int, int, int, int)", self.keyboard_callback
            )
            self._mouse_callback = ffi.callback(
                "void(GLFWwindow*, double, double)", self.mouse_callback
            )
            self._mouse_button_callback = ffi.callback(
                "void(GLFWwindow*, int, int, int)", self.mouse_button_callback
            )
            self._resize_callback = ffi.callback(
                "void(GLFWwindow*, int, int)", self.resize_callback
            )
            self._char_callback = ffi.callback(
                "void(GLFWwindow*, unsigned int)", self.char_callback
            )
            self._scroll_callback = ffi.callback(
                "void(GLFWwindow*, double, double)", self.scroll_callback
            )

            rl.glfwSetKeyCallback(
                self.window,
                self._keyboard_callback,
            )
            rl.glfwSetCursorPosCallback(
                self.window,
                self._mouse_callback,
            )
            rl.glfwSetMouseButtonCallback(
                self.window,
                self._mouse_button_callback,
            )
            rl.glfwSetWindowSizeCallback(
                self.window,
                self._resize_callback,
            )
            rl.glfwSetCharCallback(
                self.window,
                self._char_callback,
            )
            rl.glfwSetScrollCallback(
                self.window,
                self._scroll_callback,
            )
        screen_width = ffi.new("int *")
        screen_height = ffi.new("int *")
        rl.glfwGetMonitorPhysicalSize(
            rl.glfwGetPrimaryMonitor(), screen_width, screen_height
        )

        # convert to int
        screen_width = screen_width[0]
        screen_height = screen_height[0]
        self.io.display_size = ImVec2(screen_width, screen_height)

        def get_clipboard_text(_ctx: imgui.internal.Context) -> str:
            return rl.glfwGetClipboardString(self.window).decode("utf-8")

        def set_clipboard_text(_ctx: imgui.internal.Context, text: str) -> None:
            rl.glfwSetClipboardString(self.window, text.encode("utf-8"))

        imgui.get_platform_io().platform_get_clipboard_text_fn = get_clipboard_text
        imgui.get_platform_io().platform_set_clipboard_text_fn = set_clipboard_text

        self._map_keys()
        self._gui_time = None

    def _create_callback(self, ctype, func):
        return ffi.callback(ctype, func)

    def _map_keys(self):
        self.key_map = {}
        key_map = self.key_map
        key_map[rl.KEY_LEFT] = imgui.Key.left_arrow
        key_map[rl.KEY_RIGHT] = imgui.Key.right_arrow

        key_map[rl.KEY_LEFT_CONTROL] = imgui.Key.left_ctrl
        key_map[rl.KEY_RIGHT_CONTROL] = imgui.Key.right_ctrl
        key_map[rl.KEY_LEFT_SHIFT] = imgui.Key.left_shift
        key_map[rl.KEY_RIGHT_SHIFT] = imgui.Key.right_shift
        key_map[rl.KEY_LEFT_ALT] = imgui.Key.left_alt
        key_map[rl.KEY_RIGHT_ALT] = imgui.Key.right_alt
        key_map[rl.KEY_LEFT_SUPER] = imgui.Key.left_super
        key_map[rl.KEY_RIGHT_SUPER] = imgui.Key.right_super

        key_map[rl.KEY_TAB] = imgui.Key.tab
        key_map[rl.KEY_LEFT] = imgui.Key.left_arrow
        key_map[rl.KEY_RIGHT] = imgui.Key.right_arrow
        key_map[rl.KEY_UP] = imgui.Key.up_arrow
        key_map[rl.KEY_DOWN] = imgui.Key.down_arrow
        key_map[rl.KEY_PAGE_UP] = imgui.Key.page_up
        key_map[rl.KEY_PAGE_DOWN] = imgui.Key.page_down
        key_map[rl.KEY_HOME] = imgui.Key.home
        key_map[rl.KEY_END] = imgui.Key.end
        key_map[rl.KEY_INSERT] = imgui.Key.insert
        key_map[rl.KEY_DELETE] = imgui.Key.delete
        key_map[rl.KEY_BACKSPACE] = imgui.Key.backspace
        key_map[rl.KEY_SPACE] = imgui.Key.space
        key_map[rl.KEY_ENTER] = imgui.Key.enter
        key_map[rl.KEY_ESCAPE] = imgui.Key.escape
        key_map[rl.KEY_KP_ENTER] = imgui.Key.keypad_enter
        key_map[rl.KEY_A] = imgui.Key.a
        key_map[rl.KEY_C] = imgui.Key.c
        key_map[rl.KEY_V] = imgui.Key.v
        key_map[rl.KEY_X] = imgui.Key.x
        key_map[rl.KEY_Y] = imgui.Key.y
        key_map[rl.KEY_Z] = imgui.Key.z

        self.modifier_map = {}
        self.modifier_map[rl.KEY_LEFT_CONTROL] = imgui.Key.mod_ctrl
        self.modifier_map[rl.KEY_RIGHT_CONTROL] = imgui.Key.mod_ctrl
        self.modifier_map[rl.KEY_LEFT_SHIFT] = imgui.Key.mod_shift
        self.modifier_map[rl.KEY_RIGHT_SHIFT] = imgui.Key.mod_shift
        self.modifier_map[rl.KEY_LEFT_ALT] = imgui.Key.mod_alt
        self.modifier_map[rl.KEY_RIGHT_ALT] = imgui.Key.mod_alt
        self.modifier_map[rl.KEY_LEFT_SUPER] = imgui.Key.mod_super
        self.modifier_map[rl.KEY_RIGHT_SUPER] = imgui.Key.mod_super

    def keyboard_callback(self, window, glfw_key: int, scancode, action, mods):
        # perf: local for faster access
        io = self.io

        if glfw_key not in self.key_map:
            return
        imgui_key = self.key_map[glfw_key]

        down = action != GLFW_RELEASE
        io.add_key_event(imgui_key, down)

        if glfw_key in self.modifier_map:
            imgui_key = self.modifier_map[glfw_key]
            io.add_key_event(imgui_key, down)

    def char_callback(self, window, char):
        io = imgui.get_io()

        if 0 < char < 0x10000:
            io.add_input_character(char)

    def resize_callback(self, window, width, height):
        self.io.display_size = ImVec2(width, height)

    def mouse_callback(self, *args, **kwargs):
        if rl.glfwGetWindowAttrib(self.window, GLFW_FOCUSED):
            x_pos = ffi.new("double *")
            y_pos = ffi.new("double *")
            rl.glfwGetCursorPos(self.window, x_pos, y_pos)
            assert x_pos and y_pos
            self.io.add_mouse_pos_event(x_pos[0], y_pos[0])
        else:
            self.io.add_mouse_pos_event(-1, -1)

    def mouse_button_callback(self, window, button, action, mods):
        self.io.add_mouse_button_event(button, action == GLFW_PRESS)

    def scroll_callback(self, window, x_offset, y_offset):
        self.io.add_mouse_wheel_event(x_offset, y_offset)

    def process_inputs(self):
        io = imgui.get_io()

        # Get window and framebuffer dimensions
        window_width, window_height = rl.GetScreenWidth(), rl.GetScreenHeight()
        fb_width, fb_height = rl.GetRenderWidth(), rl.GetRenderHeight()

        # Set display size and framebuffer scale
        io.display_size = ImVec2(window_width, window_height)
        io.display_framebuffer_scale = compute_fb_scale(
            (window_width, window_height), (fb_width, fb_height)
        )  # type: ignore

        # Calculate delta time
        current_fps = rl.GetFPS() or 60
        current_time = rl.glfwGetTime()
        io.delta_time = 1.0 / current_fps

        if self._gui_time:
            io.delta_time = current_time - self._gui_time
        if io.delta_time <= 0.0:
            io.delta_time = 1.0 / 1000.0

        # Update GUI time
        self._gui_time = current_time

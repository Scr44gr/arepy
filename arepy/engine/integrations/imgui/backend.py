# Based on https://github.com/pthom/imgui_bundle/blob/main/bindings/imgui_bundle/python_backends/glfw_backend.py
from __future__ import absolute_import

from typing import Dict

import moderngl
import raylib as rl
from imgui_bundle import ImVec2, imgui
from imgui_bundle.python_backends import compute_fb_scale
from pyray import ffi
from raylib.defines import GLFW_FOCUSED, GLFW_PRESS, GLFW_RELEASE

from ....event_manager import EventManager
from ....event_manager.events.keyboard_event import (
    Key,
    KeyboardPressedEvent,
    KeyboardReleasedEvent,
)
from ....event_manager.events.mouse_event import (
    MouseMovedEvent,
    MousePressedEvent,
    MouseReleasedEvent,
    MouseWheelEvent,
)
from .moderngl_renderer import ModernGLRenderer

GlfwKey = int


class ImguiBackend(ModernGLRenderer):
    key_map: Dict[GlfwKey, imgui.Key]
    modifier_map: Dict[GlfwKey, imgui.Key]

    def __init__(
        self,
        event_manager: EventManager,
        attach_callbacks: bool = True,
    ):
        super(ImguiBackend, self).__init__(ctx=moderngl.get_context())
        self.window = rl.glfwGetCurrentContext()
        if attach_callbacks:
            event_manager.subscribe(KeyboardPressedEvent, self.keyboard_callback)
            event_manager.subscribe(KeyboardReleasedEvent, self.keyboard_callback)
            event_manager.subscribe(MouseMovedEvent, self.mouse_callback)
            event_manager.subscribe(MousePressedEvent, self.mouse_button_callback)
            event_manager.subscribe(MouseReleasedEvent, self.mouse_button_callback)
            event_manager.subscribe(MouseWheelEvent, self.scroll_callback)

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

    def keyboard_callback(self, event: KeyboardPressedEvent | KeyboardReleasedEvent):
        io = self.io
        event_key = event.key.value
        if event_key not in self.key_map:
            return

        imgui_key = self.key_map[event_key]

        down = isinstance(event, KeyboardPressedEvent)
        io.add_key_event(imgui_key, down)

        if event_key in self.modifier_map:
            imgui_key = self.modifier_map[event_key]
            io.add_key_event(imgui_key, down)

    def char_callback(self, event: KeyboardPressedEvent):
        io = imgui.get_io()
        char = event.key.value

        if 0 < char < 0x10000:
            io.add_input_character(char)

    def resize_callback(self, window, width, height):
        self.io.display_size = ImVec2(width, height)

    def mouse_callback(self, _: MouseMovedEvent):
        if rl.glfwGetWindowAttrib(self.window, GLFW_FOCUSED):
            x_pos = ffi.new("double *")
            y_pos = ffi.new("double *")
            rl.glfwGetCursorPos(self.window, x_pos, y_pos)
            assert x_pos and y_pos
            self.io.add_mouse_pos_event(x_pos[0], y_pos[0])
        else:
            self.io.add_mouse_pos_event(-1, -1)

    def mouse_button_callback(self, event: MousePressedEvent | MouseReleasedEvent):
        self.io.add_mouse_button_event(
            event.button.value, isinstance(event, MousePressedEvent)
        )

    def scroll_callback(self, event: MouseWheelEvent):
        x_offset = event.x_offset
        y_offset = event.y_offset
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

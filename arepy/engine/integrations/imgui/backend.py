# Based on https://github.com/pthom/imgui_bundle/blob/main/bindings/imgui_bundle/python_backends/glfw_backend.py
# thx @electronstudio for the Backend implementation https://github.com/Scr44gr/raylib-imgui/pull/1
# type: ignore
from __future__ import absolute_import

from typing import Dict

import moderngl
import raylib as rl
from imgui_bundle import ImVec2, imgui
from imgui_bundle.python_backends import compute_fb_scale

from .moderngl_renderer import ModernGLRenderer

RaylibKey = int


class ImguiBackend(ModernGLRenderer):
    key_map: Dict[RaylibKey, imgui.Key]

    def __init__(self):
        super(ImguiBackend, self).__init__(ctx=moderngl.get_context())

        def get_clipboard_text(_ctx: imgui.internal.Context) -> str:
            return rl.ffi.string(rl.GetClipboardText()).decode("utf-8")  # type: ignore

        def set_clipboard_text(_ctx: imgui.internal.Context, text: str) -> None:
            rl.SetClipboardText(text.encode("utf-8"))

        self.io.mouse_pos = ImVec2(0, 0)

        self.io.backend_flags = (
            imgui.BackendFlags_.has_set_mouse_pos
            | imgui.BackendFlags_.has_mouse_cursors
            | imgui.BackendFlags_.has_gamepad
        )

        imgui.get_platform_io().platform_get_clipboard_text_fn = get_clipboard_text
        imgui.get_platform_io().platform_set_clipboard_text_fn = set_clipboard_text

        self._map_keys()

        self.last_frame_focused = False
        self.last_control_pressed = False
        self.last_shift_pressed = False
        self.last_alt_pressed = False
        self.last_super_pressed = False

    def _map_keys(self):
        self.key_map = {}
        key_map = self.key_map

        key_map[rl.KEY_APOSTROPHE] = imgui.Key.apostrophe
        key_map[rl.KEY_COMMA] = imgui.Key.comma
        key_map[rl.KEY_MINUS] = imgui.Key.minus
        key_map[rl.KEY_PERIOD] = imgui.Key.period
        key_map[rl.KEY_SLASH] = imgui.Key.slash
        key_map[rl.KEY_ZERO] = imgui.Key._0
        key_map[rl.KEY_ONE] = imgui.Key._1
        key_map[rl.KEY_TWO] = imgui.Key._2
        key_map[rl.KEY_THREE] = imgui.Key._3
        key_map[rl.KEY_FOUR] = imgui.Key._4
        key_map[rl.KEY_FIVE] = imgui.Key._5
        key_map[rl.KEY_SIX] = imgui.Key._6
        key_map[rl.KEY_SEVEN] = imgui.Key._7
        key_map[rl.KEY_EIGHT] = imgui.Key._8
        key_map[rl.KEY_NINE] = imgui.Key._9
        key_map[rl.KEY_SEMICOLON] = imgui.Key.semicolon
        key_map[rl.KEY_EQUAL] = imgui.Key.equal
        key_map[rl.KEY_A] = imgui.Key.a
        key_map[rl.KEY_B] = imgui.Key.b
        key_map[rl.KEY_C] = imgui.Key.c
        key_map[rl.KEY_D] = imgui.Key.d
        key_map[rl.KEY_E] = imgui.Key.e
        key_map[rl.KEY_F] = imgui.Key.f
        key_map[rl.KEY_G] = imgui.Key.g
        key_map[rl.KEY_H] = imgui.Key.h
        key_map[rl.KEY_I] = imgui.Key.i
        key_map[rl.KEY_J] = imgui.Key.j
        key_map[rl.KEY_K] = imgui.Key.k
        key_map[rl.KEY_L] = imgui.Key.l
        key_map[rl.KEY_M] = imgui.Key.m
        key_map[rl.KEY_N] = imgui.Key.n
        key_map[rl.KEY_O] = imgui.Key.o
        key_map[rl.KEY_P] = imgui.Key.p
        key_map[rl.KEY_Q] = imgui.Key.q
        key_map[rl.KEY_R] = imgui.Key.r
        key_map[rl.KEY_S] = imgui.Key.s
        key_map[rl.KEY_T] = imgui.Key.t
        key_map[rl.KEY_U] = imgui.Key.u
        key_map[rl.KEY_V] = imgui.Key.v
        key_map[rl.KEY_W] = imgui.Key.w
        key_map[rl.KEY_X] = imgui.Key.x
        key_map[rl.KEY_Y] = imgui.Key.y
        key_map[rl.KEY_Z] = imgui.Key.z
        key_map[rl.KEY_SPACE] = imgui.Key.space
        key_map[rl.KEY_ESCAPE] = imgui.Key.escape
        key_map[rl.KEY_ENTER] = imgui.Key.enter
        key_map[rl.KEY_TAB] = imgui.Key.tab
        key_map[rl.KEY_BACKSPACE] = imgui.Key.backspace
        key_map[rl.KEY_INSERT] = imgui.Key.insert
        key_map[rl.KEY_DELETE] = imgui.Key.delete
        key_map[rl.KEY_RIGHT] = imgui.Key.right_arrow
        key_map[rl.KEY_LEFT] = imgui.Key.left_arrow
        key_map[rl.KEY_DOWN] = imgui.Key.down_arrow
        key_map[rl.KEY_UP] = imgui.Key.up_arrow
        key_map[rl.KEY_PAGE_UP] = imgui.Key.page_up
        key_map[rl.KEY_PAGE_DOWN] = imgui.Key.page_down
        key_map[rl.KEY_HOME] = imgui.Key.home
        key_map[rl.KEY_END] = imgui.Key.end
        key_map[rl.KEY_CAPS_LOCK] = imgui.Key.caps_lock
        key_map[rl.KEY_SCROLL_LOCK] = imgui.Key.scroll_lock
        key_map[rl.KEY_NUM_LOCK] = imgui.Key.num_lock
        key_map[rl.KEY_PRINT_SCREEN] = imgui.Key.print_screen
        key_map[rl.KEY_PAUSE] = imgui.Key.pause
        key_map[rl.KEY_F1] = imgui.Key.f1
        key_map[rl.KEY_F2] = imgui.Key.f2
        key_map[rl.KEY_F3] = imgui.Key.f3
        key_map[rl.KEY_F4] = imgui.Key.f4
        key_map[rl.KEY_F5] = imgui.Key.f5
        key_map[rl.KEY_F6] = imgui.Key.f6
        key_map[rl.KEY_F7] = imgui.Key.f7
        key_map[rl.KEY_F8] = imgui.Key.f8
        key_map[rl.KEY_F9] = imgui.Key.f9
        key_map[rl.KEY_F10] = imgui.Key.f10
        key_map[rl.KEY_F11] = imgui.Key.f11
        key_map[rl.KEY_F12] = imgui.Key.f12
        key_map[rl.KEY_LEFT_SHIFT] = imgui.Key.left_shift
        key_map[rl.KEY_LEFT_CONTROL] = imgui.Key.left_ctrl
        key_map[rl.KEY_LEFT_ALT] = imgui.Key.left_alt
        key_map[rl.KEY_LEFT_SUPER] = imgui.Key.left_super
        key_map[rl.KEY_RIGHT_SHIFT] = imgui.Key.right_shift
        key_map[rl.KEY_RIGHT_CONTROL] = imgui.Key.right_ctrl
        key_map[rl.KEY_RIGHT_ALT] = imgui.Key.right_alt
        key_map[rl.KEY_RIGHT_SUPER] = imgui.Key.right_super
        key_map[rl.KEY_KB_MENU] = imgui.Key.menu
        key_map[rl.KEY_LEFT_BRACKET] = imgui.Key.left_bracket
        key_map[rl.KEY_BACKSLASH] = imgui.Key.backslash
        key_map[rl.KEY_RIGHT_BRACKET] = imgui.Key.right_bracket
        key_map[rl.KEY_GRAVE] = imgui.Key.grave_accent
        key_map[rl.KEY_KP_1] = imgui.Key.keypad1
        key_map[rl.KEY_KP_2] = imgui.Key.keypad2
        key_map[rl.KEY_KP_3] = imgui.Key.keypad3
        key_map[rl.KEY_KP_4] = imgui.Key.keypad4
        key_map[rl.KEY_KP_5] = imgui.Key.keypad5
        key_map[rl.KEY_KP_6] = imgui.Key.keypad6
        key_map[rl.KEY_KP_7] = imgui.Key.keypad7
        key_map[rl.KEY_KP_8] = imgui.Key.keypad8
        key_map[rl.KEY_KP_9] = imgui.Key.keypad9
        key_map[rl.KEY_KP_DECIMAL] = imgui.Key.keypad_decimal
        key_map[rl.KEY_KP_DIVIDE] = imgui.Key.keypad_divide
        key_map[rl.KEY_KP_MULTIPLY] = imgui.Key.keypad_multiply
        key_map[rl.KEY_KP_SUBTRACT] = imgui.Key.keypad_subtract
        key_map[rl.KEY_KP_ADD] = imgui.Key.keypad_add
        key_map[rl.KEY_KP_ENTER] = imgui.Key.keypad_enter
        key_map[rl.KEY_KP_EQUAL] = imgui.Key.keypad_equal

    def _set_mouse_event(self, ray_mouse, imgui_mouse):
        if rl.IsMouseButtonPressed(ray_mouse):
            self.io.add_mouse_button_event(imgui_mouse, True)
        elif rl.IsMouseButtonReleased(ray_mouse):
            self.io.add_mouse_button_event(imgui_mouse, False)

    def _handle_gamepadbutton_event(self, button, key):
        if rl.IsGamepadButtonPressed(0, button):
            self.io.add_key_event(key, True)
        elif rl.IsGamepadButtonReleased(0, button):
            self.io.add_key_event(key, False)

    def _handle_gamepad_stick_event(self, axis, negKey, posKey):
        deadZone = 0.20
        axisValue = rl.GetGamepadAxisMovement(0, axis)

        self.io.add_key_analog_event(
            negKey, axisValue < -deadZone, -axisValue if axisValue < -deadZone else 0
        )
        self.io.add_key_analog_event(
            posKey, axisValue > deadZone, axisValue if axisValue > deadZone else 0
        )

    def process_inputs(self):
        io = self.io

        # Get window and framebuffer dimensions
        window_width, window_height = rl.GetScreenWidth(), rl.GetScreenHeight()
        fb_width, fb_height = rl.GetRenderWidth(), rl.GetRenderHeight()

        # Set display size and framebuffer scale
        # TODO: this may need to be more complex on some platforms
        # see https://github.com/raylib-extras/rlImGui/blob/583d4fea67e67d431319974f0625f680d3840dfb/rlImGui.cpp#L108
        io.display_size = ImVec2(window_width, window_height)
        io.display_framebuffer_scale = compute_fb_scale(
            (window_width, window_height), (fb_width, fb_height)
        )  # type: ignore

        io.delta_time = max(rl.GetFrameTime(), 0.001)

        focused = rl.IsWindowFocused()
        if focused != self.last_frame_focused:
            io.add_focus_event(focused)
        self.last_frame_focused = focused

        ctrl_down = rl.IsKeyDown(rl.KEY_RIGHT_CONTROL) or rl.IsKeyDown(
            rl.KEY_LEFT_CONTROL
        )
        if ctrl_down != self.last_control_pressed:
            io.add_key_event(imgui.Key.mod_ctrl, ctrl_down)
        self.last_control_pressed = ctrl_down

        shift_down = rl.IsKeyDown(rl.KEY_RIGHT_SHIFT) or rl.IsKeyDown(rl.KEY_LEFT_SHIFT)
        if shift_down != self.last_shift_pressed:
            io.add_key_event(imgui.Key.mod_shift, shift_down)
        self.last_shift_pressed = shift_down

        alt_down = rl.IsKeyDown(rl.KEY_RIGHT_ALT) or rl.IsKeyDown(rl.KEY_LEFT_ALT)
        if alt_down != self.last_alt_pressed:
            io.add_key_event(imgui.Key.mod_alt, alt_down)
        self.last_alt_pressed = alt_down

        super_down = rl.IsKeyDown(rl.KEY_RIGHT_SUPER) or rl.IsKeyDown(rl.KEY_LEFT_SUPER)
        if super_down != self.last_super_pressed:
            io.add_key_event(imgui.Key.mod_super, super_down)
        self.last_super_pressed = super_down

        for ray_key, imgui_key in self.key_map.items():
            if rl.IsKeyReleased(ray_key):
                io.add_key_event(imgui_key, False)
            elif rl.IsKeyPressed(ray_key):
                io.add_key_event(imgui_key, True)

        if io.want_capture_keyboard:
            pressed = rl.GetCharPressed()
            while pressed != 0:
                io.add_input_character(pressed)
                pressed = rl.GetCharPressed()

        if not io.want_set_mouse_pos:
            io.add_mouse_pos_event(rl.GetMouseX(), rl.GetMouseY())

        self._set_mouse_event(rl.MOUSE_BUTTON_LEFT, 0)
        self._set_mouse_event(rl.MOUSE_BUTTON_RIGHT, 1)
        self._set_mouse_event(rl.MOUSE_BUTTON_MIDDLE, 2)
        self._set_mouse_event(rl.MOUSE_BUTTON_FORWARD, 3)
        self._set_mouse_event(rl.MOUSE_BUTTON_BACK, 4)

        mouse_wheel = rl.GetMouseWheelMoveV()
        io.add_mouse_wheel_event(mouse_wheel.x, mouse_wheel.y)

        if (
            io.config_flags & imgui.ConfigFlags_.nav_enable_gamepad
        ) and rl.IsGamepadAvailable(0):
            self._handle_gamepadbutton_event(
                rl.GAMEPAD_BUTTON_LEFT_FACE_UP, imgui.Key.gamepad_dpad_up
            )
            self._handle_gamepadbutton_event(
                rl.GAMEPAD_BUTTON_LEFT_FACE_RIGHT, imgui.Key.gamepad_dpad_right
            )
            self._handle_gamepadbutton_event(
                rl.GAMEPAD_BUTTON_LEFT_FACE_DOWN, imgui.Key.gamepad_dpad_down
            )
            self._handle_gamepadbutton_event(
                rl.GAMEPAD_BUTTON_LEFT_FACE_LEFT, imgui.Key.gamepad_dpad_left
            )

            self._handle_gamepadbutton_event(
                rl.GAMEPAD_BUTTON_RIGHT_FACE_UP, imgui.Key.gamepad_face_up
            )
            self._handle_gamepadbutton_event(
                rl.GAMEPAD_BUTTON_RIGHT_FACE_RIGHT, imgui.Key.gamepad_face_left
            )
            self._handle_gamepadbutton_event(
                rl.GAMEPAD_BUTTON_RIGHT_FACE_DOWN, imgui.Key.gamepad_face_down
            )
            self._handle_gamepadbutton_event(
                rl.GAMEPAD_BUTTON_RIGHT_FACE_LEFT, imgui.Key.gamepad_face_left
            )

            self._handle_gamepadbutton_event(
                rl.GAMEPAD_BUTTON_LEFT_TRIGGER_1, imgui.Key.gamepad_l1
            )
            self._handle_gamepadbutton_event(
                rl.GAMEPAD_BUTTON_LEFT_TRIGGER_2, imgui.Key.gamepad_l2
            )
            self._handle_gamepadbutton_event(
                rl.GAMEPAD_BUTTON_RIGHT_TRIGGER_1, imgui.Key.gamepad_r1
            )
            self._handle_gamepadbutton_event(
                rl.GAMEPAD_BUTTON_RIGHT_TRIGGER_2, imgui.Key.gamepad_r2
            )
            self._handle_gamepadbutton_event(
                rl.GAMEPAD_BUTTON_LEFT_THUMB, imgui.Key.gamepad_l3
            )
            self._handle_gamepadbutton_event(
                rl.GAMEPAD_BUTTON_RIGHT_THUMB, imgui.Key.gamepad_r3
            )

            self._handle_gamepadbutton_event(
                rl.GAMEPAD_BUTTON_MIDDLE_LEFT, imgui.Key.gamepad_start
            )
            self._handle_gamepadbutton_event(
                rl.GAMEPAD_BUTTON_MIDDLE_RIGHT, imgui.Key.gamepad_back
            )

            self._handle_gamepad_stick_event(
                rl.GAMEPAD_AXIS_LEFT_X,
                imgui.Key.gamepad_l_stick_left,
                imgui.Key.gamepad_l_stick_right,
            )
            self._handle_gamepad_stick_event(
                rl.GAMEPAD_AXIS_LEFT_Y,
                imgui.Key.gamepad_l_stick_up,
                imgui.Key.gamepad_l_stick_down,
            )

            self._handle_gamepad_stick_event(
                rl.GAMEPAD_AXIS_RIGHT_X,
                imgui.Key.gamepad_r_stick_left,
                imgui.Key.gamepad_r_stick_right,
            )
            self._handle_gamepad_stick_event(
                rl.GAMEPAD_AXIS_RIGHT_Y,
                imgui.Key.gamepad_r_stick_up,
                imgui.Key.gamepad_r_stick_down,
            )

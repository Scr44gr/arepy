from dataclasses import dataclass
from typing import Any, Optional, Protocol


class ImGuiRendererRepository(Protocol):
    def __init__(self, window: int): ...
    def render(self, data: Any): ...
    def process_inputs(self): ...


@dataclass(frozen=True)
class Default:
    def __init__(self, *args, **kwargs):
        pass

    def __getattr__(self, item):
        return self

    def __call__(self, *args, **kwargs):
        return False


class ImGui(Protocol):
    """A helper class to interact with the ImGui library"""

    def get_draw_data(self) -> Any:
        """Get the draw data"""
        ...

    def create_context(self):
        """Create a new ImGui Context"""
        ...

    def render(self):
        """Render the ImGui frame"""
        ...

    def shutdown(self):
        """Shutdown the ImGui context"""
        ...

    def get_io(self):
        """Get the ImGui IO object"""
        ...

    def accept_drag_drop_payload(self, type: str, flags: int):
        """Accept a drag and drop payload

        Args:
            type: The type of the payload
            flags: The flags of the payload
        """
        ...

    def align_text_to_frame_padding(self):
        """Align text to the frame padding"""
        ...

    def arrow_button(self, label: str, direction: int) -> bool:
        """Create an arrow button

        Args:
            label: The label of the button
            direction: The direction of the arrow

        Returns:
            bool: True if the button was clicked
        """
        ...

    def begin_child(
        self, id: str, width: float, height: float, border: bool, flags: int
    ):
        """Begin a new child window

        Args:
            id: The id of the child window
            width: The width of the child window
            height: The height of the child window
            border: Whether the child window has a border
            flags: The flags of the child window
        """
        ...

    def end_child(self):
        """End the current child window"""
        ...

    def begin_combo(self, label: str, preview_value: str, flags: int):
        """Begin a new combo box

        Args:
            label: The label of the combo box
            preview_value: The preview value of the combo box
            flags: The flags of the combo box
        """
        ...

    def begin_drag_drop_source(self, flags: int):
        """Begin a new drag and drop source

        Set the current item as a drag and drop source. If dragging is True, you can call set_drag_drop_payload() and end_drag_drop_source().
        Use with with to automatically call end_drag_drop_source() if necessary.

        Args:
            flags: The flags of the drag and drop source
        """
        ...

    def begin_tab_item(self, label: str, open: bool, flags: int) -> Default:
        """Begin a new tab item

        Args:
            label: The label of the tab item
            open: Whether the tab item is open
            flags: The flags of the tab item
        """
        ...

    def begin_tab_bar(self, id: str, flags: int) -> Default:
        """Begin a new tab bar

        Args:
            id: The id of the tab bar
            flags: The flags of the tab bar
        """
        ...

    def begin_main_menu_bar(self):
        """Begin a new main menu bar"""
        ...

    def begin_menu(self, label: str, enabled: bool) -> bool:
        """Begin a new menu

        Args:
            label: The label of the menu
            enabled: Whether the menu is enabled

        Returns:
            bool: True if the menu was clicked
        """
        ...

    def get_window_draw_list(self) -> Default:
        """Get the window draw list"""
        ...

    def get_content_region_available(self) -> tuple[float, float]:
        """Get the content region available"""
        ...

    def same_line(self, offset_from_start_x: float = 0.0, spacing: float = -1.0):
        """Move the cursor to the same line

        Args:
            offset_from_start_x: The offset from the start x
            spacing: The spacing
        """
        ...

    def new_frame(self):
        """Start a new ImGui frame"""
        ...

    def button(self, label: str) -> bool:
        """Create a button

        Args:
            label: The label of the button

        Returns:
            bool: True if the button was clicked
        """
        ...

    def text(self, text: str):
        """Print text

        Args:
            text: The text to print
        """
        ...

    def begin(self, name: str, open: bool = True, flags: int = 0):
        """Begin a new window

        Args:
            name: The name of the window
            open: Whether the window is open
        """
        ...

    def end(self):
        """End the current window"""
        ...

    def end_tab_item(self):
        """End the current tab item"""
        ...

    def end_tab_bar(self):
        """End the current tab bar"""
        ...

    def end_main_menu_bar(self):
        """End the current main menu bar"""
        ...

    def end_menu(self):
        """End the current menu"""
        ...

    def open_popup(self, id: str):
        """Open a popup

        Args:
            id: The id of the popup
        """
        ...

    def begin_popup(self, id: str):
        """Begin a new popup

        Args:
            id: The id of the popup
        """
        ...

    def end_popup(self):
        """End the current popup"""
        ...

    def input_text(self, label: str, value: str, buffer_length: int):
        """Create an input text field

        Args:
            label: The label of the input field
            value: The value of the input field
            buffer_length: The length of the buffer
        """
        ...

    def input_text_multiline(
        self,
        label: str,
        value: str,
        buffer_length: int,
        width: float,
        height: float,
        flags: int = 0,
        callback: Optional[Default] = None,
    ):
        """Create a multiline input text field

        Args:
            label: The label of the input field
            value: The value of the input field
            buffer_length: The length of the buffer
            width: The width of the input field
            height: The height of the input field
            flags: The flags of the input field
            callback: The callback of the input field
        """
        ...

    def input_float(self, label: str, value: float, step: float, step_fast: float):
        """Create a float input field

        Args:
            label: The label of the input field
            value: The value of the input field
            step: The step of the input field
            step_fast: The fast step of the input field
        """
        ...

    def get_cursor_screen_pos(self) -> tuple[float, float]:
        """Get the cursor screen position"""
        ...

    def slider_int(
        self, label: str, value: int, min_value: int, max_value: int, format: str
    ):
        """Create an integer slider

        Args:
            label: The label of the slider
            value: The value of the slider
            min_value: The minimum value of the slider
            max_value: The maximum value of the slider
            format: The format of the slider
        """
        ...

    def slider_float(
        self,
        label: str,
        value: float,
        min_value: float,
        max_value: float,
        format: str,
        power: float,
    ):
        """Create a float slider

        Args:
            label: The label of the slider
            value: The value of the slider
            min_value: The minimum value of the slider
            max_value: The maximum value of the slider
            format: The format of the slider
            power: The power of the slider
        """
        ...

    def menu_item(
        self, label: str, shortcut: str, selected: bool, enabled: bool
    ) -> tuple[bool, bool]:
        """Create a menu item

        Args:
            label: The label of the menu item
            shortcut: The shortcut of the menu item
            selected: Whether the menu item is selected
            enabled: Whether the menu item is enabled

        Returns:
            bool: True if the menu item was clicked
        """
        ...

    def checkbox(self, label: str, state: bool):
        """Create a checkbox

        Args:
            label: The label of the checkbox
            value: The value of the checkbox
        """
        ...

    def radio_button(self, label: str, active: bool):
        """Create a radio button

        Args:
            label: The label of the radio button
            active: Whether the radio button is active
        """
        ...

    def set_next_window_size(self, width: int, height: int):
        """Set the size of the next window

        Args:
            width: The width of the window
            height: The height of the window
        """
        ...

    def set_next_window_position(self, x: int, y: int):
        """Set the position of the next window

        Args:
            x: The x position of the window
            y: The y position of the window
        """
        ...

    def set_next_window_size_constraints(
        self, min_width: int, min_height: int, max_width: int, max_height: int
    ):
        """Set the size constraints of the next window

        Args:
            min_width: The minimum width of the window
            min_height: The minimum height of the window
            max_width: The maximum width of the window
            max_height: The maximum height of the window
        """
        ...

    def set_next_window_content_size(self, width: int, height: int):
        """Set the content size of the next window

        Args:
            width: The width of the content
            height: The height of the content
        """
        ...

    def set_next_window_collapsed(self, collapsed: bool, cond: int):
        """Set the collapsed state of the next window

        Args:
            collapsed: Whether the window is collapsed
            cond: The condition to set the collapsed state
        """
        ...

    def set_next_window_focus(self):
        """Set the focus of the next window"""
        ...

    def set_next_window_bg_alpha(self, alpha: float):
        """Set the background alpha of the next window

        Args:
            alpha: The alpha value of the background
        """
        ...

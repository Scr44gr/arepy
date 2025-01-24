#
from dataclasses import dataclass
from typing import Any, Optional, Protocol, Tuple


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


class Imgui(Protocol):
    """A helper class to interact with the ImGui library"""

    def get_draw_data(self) -> Any:
        """Get the draw data"""
        ...

    def create_context(self) -> None:
        """Create a new ImGui Context"""
        ...

    def render(self) -> None:
        """Render the ImGui frame"""
        ...

    def shutdown(self) -> None:
        """Shutdown the ImGui context"""
        ...

    def get_io(self) -> Any:
        """Get the ImGui IO object"""
        ...

    def image(
        self,
        texture_id: int,
        size: Tuple[int, int],
        uv0: Tuple[float, float] = (0.0, 0.0),
        uv1: Tuple[float, float] = (1.0, 1.0),
        tint_col: Optional[Tuple[float, float, float, float]] = None,
        border_col: Optional[Tuple[float, float, float, float]] = None,
    ) -> None:
        """Create an image

        Args:
            texture_id: The id of the texture
            size: The size of the image (width, height)
            uv0: The UV coordinates for the top-left corner (default: (0.0, 0.0))
            uv1: The UV coordinates for the bottom-right corner (default: (1.0, 1.0))
            tint_col: The tint color (default: None)
            border_col: The border color (default: None)
        """
        ...

    def accept_drag_drop_payload(self, type: str, flags: int) -> Any:
        """Accept a drag and drop payload

        Args:
            type: The type of the payload
            flags: The flags of the payload

        Returns:
            Any: The payload data
        """
        ...

    def align_text_to_frame_padding(self) -> None:
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
        self, id: str, width: float, height: float, border: bool = False, flags: int = 0
    ) -> bool:
        """Begin a new child window

        Args:
            id: The id of the child window
            width: The width of the child window
            height: The height of the child window
            border: Whether the child window has a border (default: False)
            flags: The flags of the child window (default: 0)

        Returns:
            bool: True if the child window is open
        """
        ...

    def end_child(self) -> None:
        """End the current child window"""
        ...

    def begin_combo(self, label: str, preview_value: str, flags: int = 0) -> bool:
        """Begin a new combo box

        Args:
            label: The label of the combo box
            preview_value: The preview value of the combo box
            flags: The flags of the combo box (default: 0)

        Returns:
            bool: True if the combo box is open
        """
        ...

    def begin_drag_drop_source(self, flags: int = 0) -> bool:
        """Begin a new drag and drop source

        Args:
            flags: The flags of the drag and drop source (default: 0)

        Returns:
            bool: True if the drag and drop source is active
        """
        ...

    def begin_tab_item(
        self, label: str, open: Optional[bool] = None, flags: int = 0
    ) -> Tuple[bool, bool]:
        """Begin a new tab item

        Args:
            label: The label of the tab item
            open: Whether the tab item is open (default: None)
            flags: The flags of the tab item (default: 0)

        Returns:
            Tuple[bool, bool]: A tuple containing (is_open, is_just_opened)
        """
        ...

    def begin_tab_bar(self, id: str, flags: int = 0) -> bool:
        """Begin a new tab bar

        Args:
            id: The id of the tab bar
            flags: The flags of the tab bar (default: 0)

        Returns:
            bool: True if the tab bar is open
        """
        ...

    def begin_main_menu_bar(self) -> bool:
        """Begin a new main menu bar

        Returns:
            bool: True if the main menu bar is open
        """
        ...

    def begin_menu(self, label: str, enabled: bool = True) -> bool:
        """Begin a new menu

        Args:
            label: The label of the menu
            enabled: Whether the menu is enabled (default: True)

        Returns:
            bool: True if the menu is open
        """
        ...

    def get_window_draw_list(self) -> Any:
        """Get the window draw list

        Returns:
            Any: The draw list
        """
        ...

    def get_content_region_available(self) -> Tuple[float, float]:
        """Get the content region available

        Returns:
            Tuple[float, float]: The available width and height
        """
        ...

    def same_line(
        self, offset_from_start_x: float = 0.0, spacing: float = -1.0
    ) -> None:
        """Move the cursor to the same line

        Args:
            offset_from_start_x: The offset from the start x (default: 0.0)
            spacing: The spacing (default: -1.0)
        """
        ...

    def new_frame(self) -> None:
        """Start a new ImGui frame"""
        ...

    def end_frame(self) -> None:
        """End the current ImGui frame"""
        ...

    def button(self, label: str, width: float = 0.0, height: float = 0.0) -> bool:
        """Create a button

        Args:
            label: The label of the button
            width: The width of the button (default: 0.0)
            height: The height of the button (default: 0.0)

        Returns:
            bool: True if the button was clicked
        """
        ...

    def text(self, text: str) -> None:
        """Print text

        Args:
            text: The text to print
        """
        ...

    def begin(self, name: str, open: Optional[bool] = None, flags: int = 0) -> bool:
        """Begin a new window

        Args:
            name: The name of the window
            open: Whether the window is open (default: None)
            flags: The flags of the window (default: 0)

        Returns:
            bool: True if the window is open
        """
        ...

    def end(self) -> None:
        """End the current window"""
        ...

    def end_tab_item(self) -> None:
        """End the current tab item"""
        ...

    def end_tab_bar(self) -> None:
        """End the current tab bar"""
        ...

    def end_main_menu_bar(self) -> None:
        """End the current main menu bar"""
        ...

    def end_menu(self) -> None:
        """End the current menu"""
        ...

    def open_popup(self, id: str) -> None:
        """Open a popup

        Args:
            id: The id of the popup
        """
        ...

    def begin_popup(self, id: str) -> bool:
        """Begin a new popup

        Args:
            id: The id of the popup

        Returns:
            bool: True if the popup is open
        """
        ...

    def end_popup(self) -> None:
        """End the current popup"""
        ...

    def input_text(
        self, label: str, value: str, buffer_length: int, flags: int = 0
    ) -> Tuple[bool, str]:
        """Create an input text field

        Args:
            label: The label of the input field
            value: The value of the input field
            buffer_length: The length of the buffer
            flags: The flags of the input field (default: 0)

        Returns:
            Tuple[bool, str]: A tuple containing (was_edited, new_value)
        """
        ...

    def input_text_multiline(
        self,
        label: str,
        value: str,
        buffer_length: int,
        width: float = 0.0,
        height: float = 0.0,
        flags: int = 0,
        callback: Optional[Any] = None,
    ) -> Tuple[bool, str]:
        """Create a multiline input text field

        Args:
            label: The label of the input field
            value: The value of the input field
            buffer_length: The length of the buffer
            width: The width of the input field (default: 0.0)
            height: The height of the input field (default: 0.0)
            flags: The flags of the input field (default: 0)
            callback: The callback of the input field (default: None)

        Returns:
            Tuple[bool, str]: A tuple containing (was_edited, new_value)
        """
        ...

    def input_float(
        self,
        label: str,
        value: float,
        step: float = 0.0,
        step_fast: float = 0.0,
        format: str = "%.3f",
        flags: int = 0,
    ) -> Tuple[bool, float]:
        """Create a float input field

        Args:
            label: The label of the input field
            value: The value of the input field
            step: The step of the input field (default: 0.0)
            step_fast: The fast step of the input field (default: 0.0)
            format: The format of the input field (default: "%.3f")
            flags: The flags of the input field (default: 0)

        Returns:
            Tuple[bool, float]: A tuple containing (was_edited, new_value)
        """
        ...

    def get_cursor_screen_pos(self) -> Tuple[float, float]:
        """Get the cursor screen position

        Returns:
            Tuple[float, float]: The x and y coordinates of the cursor
        """
        ...

    def slider_int(
        self,
        label: str,
        value: int,
        min_value: int,
        max_value: int,
        format: str = "%d",
        flags: int = 0,
    ) -> Tuple[bool, int]:
        """Create an integer slider

        Args:
            label: The label of the slider
            value: The value of the slider
            min_value: The minimum value of the slider
            max_value: The maximum value of the slider
            format: The format of the slider (default: "%d")
            flags: The flags of the slider (default: 0)

        Returns:
            Tuple[bool, int]: A tuple containing (was_edited, new_value)
        """
        ...

    def slider_float(
        self,
        label: str,
        value: float,
        min_value: float,
        max_value: float,
        format: str = "%.3f",
        power: float = 1.0,
        flags: int = 0,
    ) -> Tuple[bool, float]:
        """Create a float slider

        Args:
            label: The label of the slider
            value: The value of the slider
            min_value: The minimum value of the slider
            max_value: The maximum value of the slider
            format: The format of the slider (default: "%.3f")
            power: The power of the slider (default: 1.0)
            flags: The flags of the slider (default: 0)

        Returns:
            Tuple[bool, float]: A tuple containing (was_edited, new_value)
        """
        ...

    def menu_item(
        self,
        label: str,
        shortcut: Optional[str] = None,
        selected: bool = False,
        enabled: bool = True,
    ) -> Tuple[bool, bool]:
        """Create a menu item

        Args:
            label: The label of the menu item
            shortcut: The shortcut of the menu item (default: None)
            selected: Whether the menu item is selected (default: False)
            enabled: Whether the menu item is enabled (default: True)

        Returns:
            Tuple[bool, bool]: A tuple containing (was_clicked, is_selected)
        """
        ...

    def checkbox(self, label: str, state: bool) -> Tuple[bool, bool]:
        """Create a checkbox

        Args:
            label: The label of the checkbox
            state: The state of the checkbox

        Returns:
            Tuple[bool, bool]: A tuple containing (was_clicked, new_state)
        """
        ...

    def radio_button(self, label: str, active: bool) -> bool:
        """Create a radio button

        Args:
            label: The label of the radio button
            active: Whether the radio button is active

        Returns:
            bool: True if the radio button was clicked
        """
        ...

    def set_next_window_size(self, width: float, height: float, cond: int = 0) -> None:
        """Set the size of the next window

        Args:
            width: The width of the window
            height: The height of the window
            cond: The condition to set the size (default: 0)
        """
        ...

    def set_next_window_position(self, x: float, y: float, cond: int = 0) -> None:
        """Set the position of the next window

        Args:
            x: The x position of the window
            y: The y position of the window
            cond: The condition to set the position (default: 0)
        """
        ...

    def set_next_window_size_constraints(
        self,
        min_width: float,
        min_height: float,
        max_width: float,
        max_height: float,
        cond: int = 0,
    ) -> None:
        """Set the size constraints of the next window

        Args:
            min_width: The minimum width of the window
            min_height: The minimum height of the window
            max_width: The maximum width of the window
            max_height: The maximum height of the window
            cond: The condition to set the constraints (default: 0)
        """
        ...

    def set_next_window_content_size(self, width: float, height: float) -> None:
        """Set the content size of the next window

        Args:
            width: The width of the content
            height: The height of the content
        """
        ...

    def set_next_window_collapsed(self, collapsed: bool, cond: int = 0) -> None:
        """Set the collapsed state of the next window

        Args:
            collapsed: Whether the window is collapsed
            cond: The condition to set the collapsed state (default: 0)
        """
        ...

    def set_next_window_focus(self) -> None:
        """Set the focus of the next window"""
        ...

    def set_next_window_bg_alpha(self, alpha: float) -> None:
        """Set the background alpha of the next window

        Args:
            alpha: The alpha value of the background
        """
        ...

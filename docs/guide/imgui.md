# ImGui in Arepy

ImGui is the optional UI layer you can use for debug panels, small tools, sliders, buttons, and quick in-game editors.

The important part is this: in Arepy, ImGui is meant to feel simple.

- you install the optional extra
- you import `imgui` from `arepy`
- you put your UI code in `SystemPipeline.RENDER_UI`
- the engine handles the frame setup and the final draw call for you

You do not need a wrapper class.
You do not need to call `imgui.new_frame()` yourself.
You do not need to call `imgui.render()` yourself.

## 1. Install the extra

If you use Arepy from PyPI:

```bash
pip install "arepy[imgui]"
```

If you are working inside this repository with `uv`:

```bash
uv sync --extra imgui
```

If you are also building the docs locally:

```bash
uv sync --extra docs --extra imgui
```

## 2. Import `imgui`

Once the extra is installed, you can import `imgui` directly from Arepy:

```python
from arepy import imgui
```

That gives you the real `imgui_bundle.imgui` module.

## 3. Put ImGui code in `RENDER_UI`

This is the recommended place for ImGui systems.

Use `RENDER` for your normal game drawing and `RENDER_UI` for Dear ImGui windows and widgets.

Here is a small example:

```python
from arepy import ArepyEngine, Display, SystemPipeline, imgui

show_demo_window = False


def debug_ui(display: Display) -> None:
    global show_demo_window

    is_open, _ = imgui.begin("Debug")
    if is_open:
        imgui.text("Hello from Arepy")
        _, show_demo_window = imgui.checkbox(
            "Show Dear ImGui demo",
            show_demo_window,
        )

        if imgui.button("Rename window"):
            display.set_window_title("Arepy Debug")
    imgui.end()

    if show_demo_window:
        show_demo_window = bool(imgui.show_demo_window(show_demo_window))


engine = ArepyEngine(title="ImGui Example")
world = engine.create_world("main")
world.add_system(SystemPipeline.RENDER_UI, debug_ui)
engine.set_current_world("main")
engine.run()
```

## 4. What the engine does for you

When ImGui is enabled, Arepy automatically does this every frame:

1. starts a new ImGui frame
2. runs your `RENDER_UI` systems
3. finishes the ImGui frame
4. sends the draw data to the backend

So your job is only to describe the UI.

## 5. Do I need to use `world.get_resource(imgui)`?

Usually, no.

For most games and tools, the simplest approach is:

```python
from arepy import imgui
```

and then use `imgui` directly.

Arepy also registers `imgui` as a global resource, so this works too:

```python
imgui_module = world.get_resource(imgui)
```

That lookup exists mostly for advanced cases or when you want to treat ImGui like another engine-managed dependency.

If you are just starting, prefer the direct import.

## 6. A simple mental model

If you are new to ImGui, think of it like this:

- `imgui.begin("Window name")` opens a window
- `imgui.text(...)` draws text inside that window
- `imgui.button(...)` draws a button and tells you if it was pressed
- `imgui.checkbox(...)` shows a checkbox and returns its new value
- `imgui.end()` closes the window you opened with `begin(...)`

You redraw the UI every frame. That is normal in Dear ImGui.

## 7. Common mistakes

- Do not call `imgui.new_frame()` yourself. The engine already does it.
- Do not call `imgui.render()` yourself. The engine already does it.
- Do not put ImGui windows in a normal `RENDER` system unless you have a very specific reason.
- Do not add a custom wrapper class just to use basic buttons, text, and checkboxes.

## 8. Smallest working example

See `examples/imgui_minimal.py` for the smallest full example currently shipped with the project.
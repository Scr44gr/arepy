# Engine Services

When you create an `ArepyEngine`, you also get a handful of shared tools that help with the everyday parts of a game.

You do not need to build these pieces yourself first. They are already there for you when the engine starts.

## Display

`Display` is the window helper.

You normally receive it in a system like this:

```python
from arepy import Display


def ui_system(display: Display) -> None:
	if display.is_window_resized():
		width, height = display.get_window_size()
		display.set_window_title(f"Game ({width}x{height})")
```

Use it when you want to:

- change the window title
- resize or move the window
- toggle fullscreen
- change the cursor
- work with clipboard text

If you think of `ArepyEngine` as the boss of the app, `Display` is the part that talks to the game window.

Common methods to look at first:

- `create_window(width, height, title)`
- `set_window_title(title)`
- `set_window_size(width, height)`
- `toggle_fullscreen()`
- `set_mouse_cursor(cursor)`
- `set_clipboard_text(text)`
- `get_time()`

## Time

`Time` is the engine's shared clock.

You inject it when gameplay logic needs a stable view of frame timing without depending on the renderer.

```python
from arepy import Time


def movement_system(time: Time) -> None:
	print(time.delta_seconds)
	print(time.elapsed_seconds)
```

It gives you values such as:

- scaled delta time for the current frame
- total elapsed time since the engine started running
- frame count
- fixed-step and accumulator fields for future scheduling and physics work

For new gameplay systems, prefer `Time` over asking `Renderer2D` for delta time directly.

Common fields to look at first:

- `delta_seconds`
- `elapsed_seconds`
- `frame_count`
- `fixed_delta_seconds`
- `accumulator_seconds`

## Timers

`Timers` is the built-in world timer service.

Every new world starts with one local `Timers` resource automatically, and the engine advances it for you once per frame. You do not need to tick it manually.

Typical setup looks like this:

```python
from arepy import Timers


@world.on_startup
def setup_timers() -> None:
	timers = world.get_world_resource(Timers)
	timers.after(1.0, lambda: print("ready"))
	timers.every(0.5, lambda: print("pulse"))
```

Or inside a system:

```python
from arepy import Time, Timers


def weapon_system(time: Time, timers: Timers) -> None:
	if timers.cooldown("player.fire", 0.2):
		print(f"fire at {time.elapsed_seconds:.2f}s")
```

Use it for:

- one-shot delays
- repeating callbacks
- cooldowns
- lightweight world-local scheduling

Common methods to look at first:

- `after(delay_seconds, callback)`
- `every(interval_seconds, callback)`
- `cancel(handle)`
- `is_active(handle)`
- `cooldown(key, duration_seconds)`
- `clear()`

## Renderer2D

`Renderer2D` is what you use for drawing most 2D things on screen.

Typical injection looks like this:

```python
from arepy import Renderer2D
from arepy.engine.renderer import Color, Rect


def hud_system(renderer: Renderer2D) -> None:
	renderer.draw_rectangle(Rect(16, 16, 180, 40), Color(25, 25, 35, 220))
	renderer.draw_text("Hello!", (28, 28), 20, Color(255, 255, 255, 255))
```

It can:

- load and draw textures
- draw rectangles, circles, lines, and text
- manage cameras
- start and finish frames
- report delta time and frame rate

For many small games, this is the renderer you will touch the most.

It still exposes `get_delta_time()`, but timing-heavy gameplay code can now depend on `Time` instead.

Common methods to look at first:

- `create_texture(path)`
- `draw_texture(texture, source, dest, color)`
- `draw_rectangle(rect, color)`
- `draw_text(text, position, font_size, color)`
- `get_delta_time()`
- `swap_buffers()`

## Renderer3D

`Renderer3D` is the 3D companion.

Example:

```python
from arepy import Renderer3D
from arepy.engine.renderer import Color
from arepy.math import Vec3


def debug_3d_system(renderer: Renderer3D) -> None:
	renderer.draw_cube(Vec3(0, 1, 0), 1.0, 1.0, 1.0, Color(80, 160, 255, 255))
	renderer.draw_grid(20, 1.0)
```

It helps you:

- load models
- create meshes such as cubes, spheres, and planes
- work with materials
- draw 3D primitives
- manage 3D cameras

If your game is mostly 2D, you may never need it. If you are building 3D scenes, this is where you start.

Common methods to look at first:

- `load_model(path)`
- `generate_mesh_cube(width, height, length)`
- `draw_model(model, position, scale, tint)`
- `draw_cube(position, width, height, length, color)`
- `begin_mode_3d(camera)`
- `draw_grid(slices, spacing)`

## Input

`Input` lets your systems react to the player.

Example:

```python
from arepy import Input, Key


def movement_input_system(input_repo: Input) -> None:
	if input_repo.is_key_down(Key.A):
		...

	if input_repo.is_key_pressed(Key.SPACE):
		...
```

It can tell you things like:

- whether a key was pressed
- whether a mouse button is down
- which gamepads are connected
- what kind of controller is connected
- how sticks and triggers are moving
- where the mouse is
- how much the wheel moved

You will often inject `Input` into systems that handle controls, menus, or camera movement.

Common methods to look at first:

- `is_key_pressed(key)`
- `is_key_down(key)`
- `get_available_gamepads()`
- `get_gamepad_device_type(gamepad_id=0)`
- `is_gamepad_button_down(button, gamepad_id=0)`
- `get_gamepad_axis_movement(axis, gamepad_id=0)`
- `is_gamepad_vibration_supported(gamepad_id=0)`
- `set_gamepad_vibration(left_motor, right_motor, duration_seconds, gamepad_id=0)`
- `is_mouse_button_pressed(button)`
- `get_mouse_position()`
- `get_mouse_wheel_delta()`
- `get_char_pressed()`

Gamepads use generic button names so the same gameplay code works for Xbox,
PlayStation, and other devices detected by raylib.

```python
from arepy import GamepadAxis, GamepadButton, GamepadDeviceType, Input


def gamepad_input_system(input_repo: Input) -> None:
	for gamepad_id in input_repo.get_available_gamepads():
		device_type = input_repo.get_gamepad_device_type(gamepad_id)
		if device_type is GamepadDeviceType.PLAYSTATION:
			...

		if input_repo.is_gamepad_button_down(
			GamepadButton.FACE_DOWN, gamepad_id
		):
			...

		if input_repo.is_gamepad_button_pressed(GamepadButton.LEFT_STICK, gamepad_id):
			if input_repo.is_gamepad_vibration_supported(gamepad_id):
				input_repo.set_gamepad_vibration(0.35, 0.85, 0.12, gamepad_id)

		move_x = input_repo.get_gamepad_axis_movement(GamepadAxis.LEFT_X, gamepad_id)
		move_y = input_repo.get_gamepad_axis_movement(GamepadAxis.LEFT_Y, gamepad_id)
		...
```

## AudioDevice

`AudioDevice` handles sound and music.

Example:

```python
from arepy import AudioDevice


def play_click(audio: AudioDevice) -> None:
	click = audio.load_sound("assets/audio/click.wav")
	audio.play_sound(click)
```

Use it to:

- load sound effects
- load music tracks
- play, pause, resume, and stop audio
- change pitch and volume

If your game needs a click sound, a jump effect, or background music, this is the tool behind it.

Common methods to look at first:

- `load_sound(path)`
- `play_sound(sound)`
- `load_music(path)`
- `play_music(music)`
- `set_sound_volume(sound, volume)`
- `set_music_volume(music, volume)`

## AssetStore

`AssetStore` is the place where you keep named assets.

It can store and retrieve:

- textures
- fonts
- sounds
- music
- models
- meshes
- materials

A simple way to think about it: `AssetStore` is your game's backpack. You put assets in once, then grab them by name whenever you need them.

## EventManager

`EventManager` is a small event system for messages inside the game.

It lets you:

- subscribe to an event type
- emit an event
- process queued events

This is useful when one part of the game wants to notify another part without calling it directly.

When you run the normal engine loop, Arepy also processes the queued events during the update phase for you.

## A small example

```python
from arepy import ArepyEngine, Input, Renderer2D, Time
from arepy.asset_store import AssetStore


engine = ArepyEngine(title="My Game")
renderer = engine.get_resource(Renderer2D)
input_repo = engine.get_resource(Input)
asset_store = engine.get_resource(AssetStore)
time = engine.get_resource(Time)
```

You usually do not fetch these services by hand inside every system, because Arepy can inject them for you. Still, it helps to know they are there and what each one is for.

## Where to go next

- Read [Resources and Systems](resources.md) to see how these services are injected into systems
- Read [Engine Lifecycle](engine-lifecycle.md) to understand when systems run
- Open [Core Services API](../api/services.md) for a service-by-service map
- Open [Display reference](../api/reference/arepy/engine/display.md)
- Open [Renderer2D reference](../api/reference/arepy/engine/renderer/renderer_2d.md)
- Open [Renderer3D reference](../api/reference/arepy/engine/renderer/renderer_3d.md)
- Open [Input reference](../api/reference/arepy/engine/input.md)
- Open [Audio reference](../api/reference/arepy/engine/audio.md)

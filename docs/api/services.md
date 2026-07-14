# Core Services API

These are the shared services and helper types used around the engine. A system
can request any registered service by annotating a parameter with its type.

## Window and display

- `Display`
- `WindowFlag`
- `CursorType`

Start here if you want to manage the window, cursor, clipboard, fullscreen state, or monitor information.

Useful entry points:

- [Display module reference](reference/arepy/engine/display.md)
- `create_window(width, height, title)`
- `set_window_title(title)`
- `toggle_fullscreen()`
- `set_mouse_cursor(cursor)`
- `get_monitor_size(monitor)`
- `get_time()`

## Timing

- `Time`
- `Timers`
- `TimerHandle`

Start here if you want stable frame timing, elapsed engine time, cooldowns, delayed callbacks, or repeating world-local timers.

Useful entry points:

- [Time module reference](reference/arepy/engine/time.md)
- `Display.get_time()`
- `Time.delta_seconds`
- `Time.elapsed_seconds`
- `Timers.after(...)`
- `Timers.every(...)`
- `Timers.cooldown(...)`
- `Timers.cancel(handle)`

## Animation

- `Animator`
- `Timeline`

Start here if you want small scripted animations, waits, method interpolation, or callback sequences without building a separate animation system.

Useful entry points:

- [Animator module reference](reference/arepy/engine/animator.md)
- `Animator.create()`
- `Timeline.to(...)`
- `Timeline.method(...)`
- `Timeline.wait(...)`
- `Timeline.call(...)`
- `Timeline.start()`
- `Timeline.cancel()`

## Rendering

- `Renderer2D`
- `Renderer3D`
- `Color`
- `Rect`
- `TextureFilter`
- `ArepyTexture`
- `ArepyFont`
- `ArepyModel`
- `ArepyMesh`
- `ArepyMaterial`

Start here if you want to draw sprites, text, shapes, models, debug primitives, or use cameras.

Useful entry points:

- [Renderer2D module reference](reference/arepy/engine/renderer/renderer_2d.md)
- [Renderer3D module reference](reference/arepy/engine/renderer/renderer_3d.md)
- `draw_texture(...)`
- `draw_text(...)`
- `draw_model(...)`
- `draw_cube(...)`
- `get_delta_time()`

Use `Time.delta_seconds` for gameplay timing. `Renderer2D.get_delta_time()` is
available when renderer-local timing is specifically needed.

Custom fonts are loaded and released directly by the renderer:
`Renderer2D.load_font_ex(...)` returns an `ArepyFont`, and
`Renderer2D.unload_font(font)` releases it. Font loading is not part of the
documented `AssetStore` workflow.

## Input

- `Input`
- `Key`
- `MouseButton`
- `GamepadButton`
- `GamepadAxis`
- `GamepadDeviceType`

Start here if you want keyboard, mouse, gamepad, wheel, or typed text state.

Useful entry points:

- [Input module reference](reference/arepy/engine/input.md)
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
- `get_char_pressed()`

## Audio

- `AudioDevice`
- `ArepySound`
- `ArepyMusic`

Start here if you want to play sound effects, stream music, or control volume and playback time.

Useful entry points:

- [Audio module reference](reference/arepy/engine/audio.md)
- `load_sound(path)`
- `play_sound(sound)`
- `load_music(path)`
- `play_music(music)`
- `seek_music_stream(music, position)`

## Assets

- `AssetStore`

Start here if you want a named store for textures, sounds, music, models,
meshes, and materials. The engine owns one shared `AssetStore`; individual
worlds must define which of those assets they own.

Useful entry points:

- [Asset store reference](reference/arepy/asset_store/asset_store.md)
- textures: `load_texture()`, `create_render_texture()`, `get_texture()`, and
  `unload_texture()`
- texture atlases: `build_texture_atlas()`, `get_texture_atlas()`, and
  `clear_texture_atlas(renderer)`
- audio: `load_sound()` / `unload_sound()` and
  `load_music()` / `unload_music()`
- 3D resources: `load_model()`, `create_mesh_*()`, `create_material()`, the
  matching getters, and the matching unload methods

Call an unload method with the same renderer or audio device used to load the
asset. `AssetStore` removes the named handle and delegates the actual release to
that backend. A world-owned asset therefore belongs in `world.on_startup` and
`world.on_shutdown`; a shared asset needs an application-level owner and must
remain loaded until its last user is finished.

## Events

- `EventManager`
- `Event`

Start here if you want loose communication between systems or gameplay modules.

Useful entry points:

- [Event manager reference](reference/arepy/event_manager/event_manager.md)
- `subscribe(EventType, callback)` and `unsubscribe(EventType, callback)`
- `emit(event)` to queue callbacks for an event instance
- `process_events()` to deliver the queue

In the normal engine loop, queued events are processed during the update phase.

## Where to keep reading

- **Public API** contains the generated modules and their member-level details.
- The engine services guide explains what each service is for in plain language.
- Read [Engine Services](../guide/engine-services.md) for examples of how these services are injected into systems.

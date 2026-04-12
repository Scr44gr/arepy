# Core Services API

These are the shared services and helper types you will most often use around the engine.

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

`Renderer2D.get_delta_time()` is still available, but `Time.delta_seconds` is now the preferred gameplay-facing timing source.

## Input

- `Input`
- `Key`
- `MouseButton`

Start here if you want keyboard, mouse, wheel, or typed text state.

Useful entry points:

- [Input module reference](reference/arepy/engine/input.md)
- `is_key_pressed(key)`
- `is_key_down(key)`
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

Start here if you want a named store for textures, fonts, sounds, music, models, meshes, and materials.

Useful entry points:

- [Asset store reference](reference/arepy/asset_store/asset_store.md)
- `add_*` and `get_*` methods on `AssetStore`

## Events

- `EventManager`
- `Event`

Start here if you want loose communication between systems or gameplay modules.

Useful entry points:

- [Event manager reference](reference/arepy/event_manager/event_manager.md)
- event subscribe / emit / process methods on `EventManager`

In the normal engine loop, queued events are processed during the update phase.

## Where to keep reading

- The generated module reference shows every method, attribute, and nested module.
- The engine services guide explains what each service is for in plain language.
- Read [Engine Services](../guide/engine-services.md) for examples of how these services are injected into systems.

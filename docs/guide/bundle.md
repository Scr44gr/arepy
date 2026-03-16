# Built-in Bundle

The `arepy.bundle` package contains reusable components and systems intended to cover common game patterns.

## Available components

The current public bundle exports:

- `RigidBody2D`
- `Sprite`
- `Transform`
- `Camera2D`
- `Camera3D`
- `Model3D`
- `Material3D`
- `Light3D`
- `Transform3D`
- `Mesh3D`

## Frequently used 2D components

### `Transform`

`Transform` stores:

- `position: Vec2`
- `scale: Vec2`
- `origin: Vec2`
- `rotation: float`

Default vectors are created per instance, so different entities do not accidentally share mutable defaults.

### `RigidBody2D`

`RigidBody2D` stores:

- `velocity: Vec2`
- `acceleration`
- `deceleration`
- `max_velocity`

### `Sprite`

`Sprite` stores:

- `asset_id`
- `src_rect`
- `z_index`
- `flipped`

## Built-in systems

The current bundle systems package exposes two reusable systems:

- `movement_system`
- `render_system`

Both use query-driven iteration over components rather than entity lookups inside the hot loop.

## Where to look next

- `examples/bunnymark.py` shows a large number of 2D moving sprites
- `examples/cubemark_3d.py` shows the 3D side of the engine

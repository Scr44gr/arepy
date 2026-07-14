# Built-in gameplay components

`arepy.bundle` contains common components and two starter systems. They are
convenient defaults, not a required game framework; custom components work
alongside them.

## 2D components

### Transform

`Transform` answers where and how a 2D object is placed:

- `position: Vec2`
- `scale: Vec2`
- `origin: Vec2`
- `rotation: float`

Each instance owns its vectors. Prefer changing their coordinates in place:

```python
transform.position.x += 20.0 * time.delta_seconds
```

### RigidBody2D

`RigidBody2D` stores movement data such as `velocity`, acceleration,
deceleration, and maximum velocity. It is data, not a full collision or rigid
body physics simulation.

### Sprite

`Sprite` identifies a loaded texture and its source region:

```python
Sprite(
    asset_id="bunny",
    src_rect=(0, 0, 32, 32),
    z_index=1,
)
```

The texture itself belongs in `AssetStore`; many entities can reference the
same handle by name.

## 3D components

The bundle also exports:

- `Transform3D`
- `Camera3D`
- `Model3D` and `Mesh3D`
- `Material3D`
- `Light3D`

`RigidBody3D` exists in its component module but is not currently re-exported
from `arepy.bundle.components`; advanced examples import it from
`arepy.bundle.components.rigidbody`.

`Camera2D` is available for 2D world-to-screen transforms.

## Bundled systems

`movement_system` moves `Transform` values from `RigidBody2D.velocity` and
bounces them inside its demonstration bounds. `render_system` draws
`Transform + Sprite` entities, using the texture atlas and batch path when one
has been built.

They are useful for examples. A real game will often replace them with systems
that know its own level bounds, collisions, animation, and draw order.

```python
from arepy.bundle.systems import movement_system, render_system


world.add_system(SystemPipeline.UPDATE, movement_system)
world.add_system(SystemPipeline.RENDER, render_system)
```

## Examples

- [`getting_started.py`](https://github.com/Scr44gr/arepy/blob/main/examples/getting_started.py)
  combines the 2D components with keyboard and mouse input.
- [`bunnymark.py`](https://github.com/Scr44gr/arepy/blob/main/examples/bunnymark.py)
  uses the same data in a large vectorized sprite batch.
- [`cubemark_3d.py`](https://github.com/Scr44gr/arepy/blob/main/examples/cubemark_3d.py)
  demonstrates the 3D renderer and transforms.

Continue with [Graphics and textures](graphics.md) for asset loading and
drawing, or [ECS basics](ecs.md) to create your own components.

# Vectors for movement and positions

Arepy's `Vec2` and `Vec3` are small mutable vectors used by transforms,
velocities, cameras, and renderer calls.

## Create and read a vector

```python
from arepy.math import Vec2, Vec3


position = Vec2(120.0, 80.0)
camera_position = Vec3(10.0, 8.0, 10.0)

print(position.x, position.y)
print(camera_position.to_tuple())
```

`vec2(x, y)`, `vec3(x, y, z)`, `vec2_zero()`, and `vec3_zero()` are convenience
constructors for the same types.

## Mutate in place in a frame loop

When an entity already owns a vector, update its coordinates:

```python
transform.position.x += body.velocity.x * time.delta_seconds
transform.position.y += body.velocity.y * time.delta_seconds
```

This keeps the same vector identity and works with `BatchQuery`'s bound vector
storage. Replacing it with `transform.position = Vec2(...)` creates another
Python object and may require a batch rebind.

In-place operators also preserve the object:

```python
velocity *= 0.95
position += velocity
```

Normal arithmetic such as `a + b`, `a - b`, or `a * 2.0` returns a new vector,
which is useful outside a hot loop or when the result must be independent.

## Direction and distance in 2D

```python
to_target = target - position
distance = abs(to_target)
direction = to_target.normalize()
```

`normalize()` returns a new unit vector. `normalize_ip()` changes the existing
vector. Both handle a zero-length vector safely; its normalized result remains
zero.

Other useful `Vec2` operations include:

- `dot(other)` for alignment;
- `distance_to(other)` for distance between points;
- `angle_to(other)` for the angle from this point to another;
- `lerp(other, t)` for interpolation;
- `rotate(angle)` for a new rotated vector.

Angles used by vector rotation are in radians. Sprite and camera rotation APIs
may use degrees, so check the receiving method rather than assuming one unit
everywhere.

## 3D helpers

`Vec3` adds a `z` coordinate plus operations commonly used with cameras and
surfaces:

```python
forward = Vec3(0.0, 0.0, -1.0)
up = Vec3(0.0, 1.0, 0.0)
travel_direction = Vec3(1.0, 0.0, -1.0).normalize()
velocity_3d = Vec3(4.0, -2.0, 1.0)
surface_direction = Vec3(1.0, 0.0, 0.0)
right = forward.cross(up)

alignment = forward.dot(travel_direction)
angle_radians = forward.angle(travel_direction)
on_surface = velocity_3d.project(surface_direction)
```

`angle()` and `project()` return safe results when one of the required vectors
has zero length.

## Point inside a rectangle

`check_collision_point_rec(point, rect)` is the lightweight 2D helper exported
by `arepy.math`. Use it for simple pointer and rectangle checks; use a dedicated
collision system when the game needs broad-phase spatial queries or complex
shapes.

Continue with [2D and 3D graphics](graphics.md), or see how
[BatchQuery vector views](queries.md#vec2-and-vec3-fields) update many vectors
together.

# Math Helpers

Arepy ships a small math layer under `arepy.math`.

## Public exports

The current public module exports:

- `Vec2`
- `vec2`
- `vec2_zero`
- `Vec3`
- `vec3`
- `vec3_zero`
- `check_collision_point_rec`

## `Vec2`

`Vec2` is the main 2D vector type used by bundle components such as `Transform` and `RigidBody2D`.

Current tests verify that it supports:

- scalar multiplication on both sides
- in-place arithmetic operations
- safe normalization of the zero vector

## `Vec3`

`Vec3` is the 3D counterpart used by 3D bundle components.

Current tests verify that it supports:

- scalar multiplication on both sides
- in-place arithmetic operations
- safe normalization of zero vectors
- safe `angle()` behavior when one vector has zero length
- safe `project()` behavior when the target vector has zero length

## Why this matters

These helpers show up all over the engine, especially in movement, transforms, and rendering-related data.

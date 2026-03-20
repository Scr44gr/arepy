<div class="arepy-hero" markdown>

![Arepy](assets/images/arepy-logo.png){ .arepy-hero__logo }

<div class="arepy-hero__title">Lightweight ECS game engine for Python</div>

<div class="arepy-hero__badges">
    <img alt="PyPI" src="https://img.shields.io/pypi/v/arepy?color=4f46e5&label=PyPI">
    <img alt="Python" src="https://img.shields.io/pypi/pyversions/arepy.svg?color=4f46e5">
    <img alt="License" src="https://img.shields.io/badge/license-MIT-f59e0b">
</div>

<div class="arepy-hero__lead" markdown>

Arepy focuses on a small API, fast iteration, and practical game development with ECS, Raylib integration, and built-in gameplay primitives.

</div>

</div>

## Why use Arepy

Arepy is designed for small-to-medium Python games that need an ECS architecture without giving up iteration speed.

1. **Small public API** — the core workflow stays centered on `ArepyEngine`, `World`, `EntityBuilder`, and `Query`.
2. **ECS-first design** — entities, components, and systems are the default way to structure gameplay logic.
3. **Typed query model** — filters such as `With[...]` and `Without[...]` are part of the public API and fit naturally into editor hints and readable system signatures.
4. **Built-in gameplay primitives** — bundles already include types like `Transform`, `RigidBody2D`, and `Sprite`.
5. **Focused documentation** — the guides stay concise and centered on the public engine workflow.

## Hello World Example

This is the smallest representative example of the current engine workflow.

```python
from arepy import ArepyEngine, Renderer2D, SystemPipeline
from arepy.bundle.components import RigidBody2D, Transform
from arepy.ecs import Entities, Query, With
from arepy.math import Vec2


def movement_system(
    query: Query[Entities, With[Transform, RigidBody2D]],
    renderer: Renderer2D,
) -> None:
    delta_time = renderer.get_delta_time()

    for transform, rigidbody in query.iter_components(Transform, RigidBody2D):
        transform.position.x += rigidbody.velocity.x * delta_time
        transform.position.y += rigidbody.velocity.y * delta_time


engine = ArepyEngine(title="Quickstart")
world = engine.create_world("main")

(
    world.create_entity()
    .with_component(Transform(position=Vec2(32, 32)))
    .with_component(RigidBody2D(velocity=Vec2(60, 20)))
    .build()
)

world.add_system(SystemPipeline.UPDATE, movement_system)
engine.set_current_world("main")
engine.run()
```

This example is complete as written and matches the public API documented in the guides.

## What this gives you

- **Engine loop** — manage worlds, resources, and frame execution.
- **ECS core** — create entities, attach components, and register systems.
- **Query iteration** — iterate matching components directly in gameplay systems.
- **Bundle integration** — start from reusable gameplay components instead of rebuilding basics.
- **Math helpers** — use `Vec2`, `Vec3`, and companion utilities across systems.

## Start here

<div class="arepy-subsection-intro" markdown>

If you are new to the project, start with installation and the ECS model before jumping into the API reference.

</div>

<div class="grid cards" markdown>

-   :material-rocket-launch: __Getting started__

    ---

    Install Arepy, create a world, add components, and run your first systems.

    [Open the guide](getting-started/index.md)

-   :material-cog-outline: __Core concepts__

    ---

    Learn how `World`, `EntityBuilder`, `Query`, `With`, and `Without` fit together.

    [Read the guide](guide/index.md)

-   :material-book-open-page-variant-outline: __API reference__

    ---

    Jump straight to the engine, ECS, bundle, and math reference pages.

    [Browse the reference](api/index.md)

</div>

## Next steps

<div class="arepy-reading-list" markdown>

1. [Installation](getting-started/installation.md) — set up the package and dependencies
2. [Quickstart](getting-started/quickstart.md) — build a minimal world and first systems
3. [Engine Lifecycle](guide/engine-lifecycle.md) — understand frame flow and orchestration
4. [ECS Basics](guide/ecs.md) — learn entities, components, and builders
5. [Queries](guide/queries.md) — compose filters and iterate efficiently
6. [Built-in Bundle](guide/bundle.md) — explore reusable gameplay primitives

</div>

## Reference map

- **Getting Started** explains installation and first-run workflow.
- **Guide** covers lifecycle, ECS, queries, resources, bundle systems, and math.
- **API Reference** documents the public engine, ECS, bundle, and math surfaces.

!!! note

    The docs stay intentionally concise and technical, with an emphasis on the public engine workflow.

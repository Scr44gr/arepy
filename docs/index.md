<div class="arepy-hero" markdown>

![Arepy](assets/images/arepy-logo.png){ .arepy-hero__logo }

<div class="arepy-hero__title">A lightweight ECS game engine for Python</div>

<div class="arepy-hero__lead" markdown>

Build a playable 2D game with familiar Python, a data-oriented ECS, Raylib-powered graphics, input, audio, and optional Dear ImGui tools.

</div>

<div class="arepy-hero__actions" markdown>

[Build your first scene](getting-started/quickstart.md){ .md-button .md-button--primary }
[Understand the ECS](guide/ecs.md){ .md-button }

</div>

</div>

<figure class="arepy-figure">
  <img class="arepy-screenshot" src="assets/images/quickstart-bunny.png" alt="The Arepy quickstart running a bunny scene in a desktop window">
  <figcaption>The quickstart uses the included bunny texture, movement systems, and live input.</figcaption>
</figure>

## Start with something you can see

The documentation follows the way a game grows: open a window, draw a sprite, move it, respond to input, add sound, and then organize the project for performance and shipping. Each guide explains the idea first, then shows the code that makes it useful.

<div class="grid cards" markdown>

-   :material-rocket-launch: __New to Arepy?__

    ---

    Install the package and build the bunny scene one small step at a time.

    [Follow the learning path](getting-started/index.md)

-   :material-shape-outline: __New to ECS?__

    ---

    Learn what entities, components, systems, worlds, and queries mean in a running game.

    [Learn the core concepts](guide/index.md)

-   :material-speedometer: __Working on performance?__

    ---

    See how pools, recycled entity slots, `Query`, and `BatchQuery` reduce work in the frame loop.

    [Read the performance guide](guide/performance.md)

-   :material-package-variant-closed: __Ready to share a build?__

    ---

    Package a project and understand which optional tools belong in a release workflow.

    [Build and ship](guide/builder.md)

</div>

## What Arepy gives you

- A `World` that owns entities, component storage, resources, and systems.
- Plain Python components and systems that keep gameplay code readable.
- Typed `Query` filters and array-oriented `BatchQuery` access for different workloads.
- Graphics, keyboard, mouse, gamepad, audio, timers, animation, and optional ImGui tools.
- Reusable gameplay components such as transforms, sprites, and 2D rigid bodies.
- A build command for turning a project into something other people can run.

Arepy is designed for Python 3.11 through 3.14. When you need exact signatures, the [public API reference](api/index.md) sits alongside the task-oriented guides instead of replacing them.

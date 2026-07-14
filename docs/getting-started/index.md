# Start Here

You do not need to understand an entire engine before drawing your first sprite. Start with a small running scene, then learn the names of the pieces as you use them.

By the end of the quickstart you will have a window with the included bunny texture, an entity that owns its game data, and systems that draw and update it.

## Your learning path

<ol class="arepy-steps">
  <li><strong><a href="installation/">Install Arepy</a></strong><br>Choose a supported Python version and the optional tools your project needs.</li>
  <li><strong><a href="quickstart/">Build your first scene</a></strong><br>Create an engine, load the bunny texture, spawn an entity, and run the game loop.</li>
  <li><strong><a href="../guide/ecs/">Understand the ECS</a></strong><br>Learn why the bunny is an entity, why its position is a component, and where movement belongs.</li>
  <li><strong><a href="../guide/input/">Add player input</a></strong><br>Read the keyboard, mouse, or a gamepad without mixing device code into every system.</li>
  <li><strong><a href="../guide/examples/">Explore complete examples</a></strong><br>Move from one sprite to animation, audio, ImGui, 3D, and stress tests.</li>
</ol>

## The five words you will see everywhere

- An **entity** is an identity for one thing in the game, such as a bunny, camera, or projectile.
- A **component** is data attached to an entity, such as a position, velocity, or sprite.
- A **system** is behavior that reads or changes matching components.
- A **world** owns a group of entities, their components, resources, and systems.
- A **query** finds the entities and components a system wants to work with.

That is enough vocabulary for the first scene. The [core concepts guide](../guide/index.md) connects these ideas with diagrams and practical examples when you are ready.

## Pick the guide that matches your goal

<div class="grid cards" markdown>

-   :material-image-outline: __Put something on screen__

    [Graphics and textures](../guide/graphics.md)

-   :material-gamepad-variant-outline: __Make it respond__

    [Keyboard, mouse, and gamepads](../guide/input.md)

-   :material-music-note-outline: __Add sound__

    [Audio](../guide/audio.md)

-   :material-wrench-outline: __Build debug tools__

    [Dear ImGui](../guide/imgui.md)

</div>

!!! tip "Learn from a running game"

    Keep the quickstart open while you read later guides. Changing one value and seeing the result is usually more memorable than reading a long list of classes.

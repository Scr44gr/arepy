# Guide

This section explains the current architecture of Arepy from the outside in.

## Recommended order

- [Engine Lifecycle](engine-lifecycle.md) explains the frame loop and world switching
- [Engine Services](engine-services.md) explains the shared tools you get with the engine
- [ECS Basics](ecs.md) explains entities, components, systems, and builders
- [Queries](queries.md) explains filters and fast iteration APIs
- [Resources and Systems](resources.md) explains dependency injection into systems
- [Built-in Bundle](bundle.md) summarizes the reusable components and systems shipped with the project
- [Math Helpers](math.md) covers the vector primitives used throughout the engine

## Design themes you will see repeatedly

- components are data containers
- systems are plain callables grouped by pipeline
- queries are signed from type annotations
- resources are injected by type name at runtime
- examples favor small, direct system code

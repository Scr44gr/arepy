# Getting Started

The fastest way to understand Arepy is:

1. install the project and run the tests
2. create an `ArepyEngine`
3. create a `World`
4. spawn entities with `world.create_entity()` and `EntityBuilder`
5. add systems to a `SystemPipeline`
6. set the current world and call `run()`

## In this section

- [Installation](installation.md) covers package installation and local development with `uv`
- [Quickstart](quickstart.md) walks through a minimal movement example

## Verify your setup early

Once dependencies are installed, these commands give you a quick health check:

```bash
uv run pytest
```

If you want a larger sample project after the quickstart, check [examples/bunnymark.py](https://github.com/Scr44gr/arepy/blob/main/examples/bunnymark.py) in the repository.

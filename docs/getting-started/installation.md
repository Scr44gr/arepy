# Installation

## Requirements

To get Arepy running, you currently need:

- Python 3.11+
- `bitarray`
- `raylib`

## Install from PyPI

```bash
pip install arepy
```

If you only want to use the engine in a game project, that is enough.

## Local setup with `uv`

```bash
git clone https://github.com/Scr44gr/arepy.git
cd arepy
uv sync --extra docs
```

This gives you the runtime dependencies plus the documentation toolchain used by this site.

## Build the docs locally

```bash
uv run mkdocs build
```

## Optional extras

If you want to work on the ImGui integration too:

```bash
uv sync --extra docs --extra imgui
```

If you are contributing to the project itself and need the full contributor workflow, use [CONTRIBUTING.md](https://github.com/Scr44gr/arepy/blob/main/CONTRIBUTING.md) as the source of truth.

## Common next steps

- Continue to [Quickstart](quickstart.md)
- Read the [Engine Lifecycle](../guide/engine-lifecycle.md)
- Explore the generated [API Reference](../api/index.md)

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

## Local development with `uv`

```bash
git clone https://github.com/Scr44gr/arepy.git
cd arepy
uv sync --extra testing --extra docs
```

This installs the runtime dependencies plus the test and documentation toolchain configured in `pyproject.toml`.

## Verify the environment

```bash
uv run pytest
uv run mkdocs build
```

## Optional extras

If you want to work on the ImGui integration too:

```bash
uv sync --extra testing --extra docs --extra imgui
```

## Common next steps

- Continue to [Quickstart](quickstart.md)
- Read the [Engine Lifecycle](../guide/engine-lifecycle.md)
- Explore the generated [API Reference](../api/index.md)

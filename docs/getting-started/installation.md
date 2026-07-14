# Installation

Arepy supports CPython **3.11, 3.12, 3.13, and 3.14**. Use a virtual environment so the engine and your game dependencies stay isolated from other Python projects.

## Create a project environment

=== "Windows (PowerShell)"

    ```powershell
    py -3.12 -m venv .venv
    .\.venv\Scripts\Activate.ps1
    python -m pip install --upgrade pip
    ```

=== "macOS and Linux"

    ```bash
    python3.12 -m venv .venv
    source .venv/bin/activate
    python -m pip install --upgrade pip
    ```

Python 3.12 is used in these commands only as an example. Pick any supported version installed on your machine.

## Install the engine

For graphics, input, audio, ECS, and the built-in gameplay bundle:

```bash
python -m pip install arepy
```

Raylib, NumPy, and the other core runtime dependencies are installed with Arepy.

Confirm that the package can be imported:

```bash
python -c "from arepy import ArepyEngine; print('Arepy is ready')"
```

## Choose optional tools

The base install stays focused on the game runtime. Add an extra only when the project needs it.

| Goal | Install command | What it adds |
| --- | --- | --- |
| Debug panels and editor-style tools | `python -m pip install "arepy[imgui]"` | Dear ImGui integration and its rendering dependencies |
| Stream a local video through the example | `python -m pip install "arepy[video]"` | PyAV decoding for `video_demo.py` |
| Package a distributable game | `python -m pip install "arepy[builder]"` | The build pipeline and packaging dependencies |
| Install every optional tool | `python -m pip install "arepy[imgui,video,builder]"` | ImGui, video, and builder support in one environment |

The `imgui` extra is for development UI such as inspectors, counters, and tuning panels. It is not required to draw your game. The `video` extra is optional because most games do not need PyAV. The `builder` extra is needed when you run `arepy --export ...` (or the compatible `arepy-build --export ...` alias).

## Work from the repository

Contributors and anyone testing an unreleased branch can use [uv](https://docs.astral.sh/uv/):

```bash
git clone https://github.com/Scr44gr/arepy.git
cd arepy
uv sync --extra docs --extra imgui --extra video --extra builder
```

Run an example from the repository environment:

```bash
uv run python examples/bunnymark.py
```

Serve the documentation locally while editing it:

```bash
uv run mkdocs serve
```

## Source builds and Rust

Arepy includes a native renderer extension. Installing a compatible wheel does not require a local Rust toolchain. If `pip` cannot find a wheel for your platform and falls back to building from source, install a current Rust toolchain and try again.

### Why the PyPI build job uses Python 3.11

The release workflow builds the native extension with Python 3.11 because
3.11 is the minimum supported ABI. PyO3's `abi3-py311` mode produces a
`cp311-abi3` wheel that can be installed by newer compatible CPython releases;
it is not a Python-3.11-only wheel. The normal CI matrix runs the package on
Python 3.11, 3.12, 3.13, and 3.14.

That means each operating-system and CPU target needs one ABI3 wheel, rather
than four otherwise-identical wheels. Release validation should still install
the finished artifacts on the supported interpreters before publishing them.

!!! warning "Check the interpreter, not only the `python` command"

    If installation reports an unsupported Python version, run `python --version`. On systems with several Python installations, activate the virtual environment again or create it with an explicit interpreter.

## Continue

Your environment is ready. Build the [first bunny scene](quickstart.md), or read the [builder guide](../guide/builder.md) if you already have a project to package.

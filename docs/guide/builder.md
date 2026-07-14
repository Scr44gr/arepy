# Build and ship a game

The Arepy builder exports a project for Windows, the web, or both. Start by
running your game from source; export only after the entrypoint and assets work
locally.

## 1. Install the build tools

```bash
pip install "arepy[builder]"
```

The Windows target uses Nuitka. The web target packages the game for Pyodide.

Build the `windows` target on Windows. The web target can be produced from the
supported development platforms.

## 2. Add a build file

Create `arepy.build.toml` next to your entrypoint:

```toml
[build]
entrypoint = "main.py"
name = "bunny-garden"
version = "1.0.0"
output_dir = "dist/bunny-garden"
assets = ["assets"]
embed_assets = false
web_title = "Bunny Garden"
```

Paths are resolved relative to this TOML file. Keep the output directory
outside every asset directory.

## 3. Export a target

=== "Windows"

    ```bash
    arepy --export windows
    ```

=== "Web"

    ```bash
    arepy --export web
    ```

=== "Both"

    ```bash
    arepy --export windows web
    ```

Use another config path with `--config`:

```bash
arepy --export windows web --config examples/bunnymark.build.toml
```

`python -m arepy` exposes the same command. `arepy-build` remains available as
a compatibility alias.

## 4. Find the artifacts

With the sample configuration, output is separated by target:

```text
dist/bunny-garden/
├── windows/
│   ├── bunny-garden.exe
│   ├── bunny-garden.assets
│   └── release.json
└── web/
    ├── index.html
    ├── runtime.js
    ├── bootstrap.js
    ├── game.zip
    ├── bunny-garden.assets
    ├── service-worker.js
    └── release.json
```

The exact Windows asset file depends on `embed_assets`: `false` keeps the
encrypted pack beside the executable; `true` produces a single-file desktop
distribution.

## Assets and paths

Configured asset directories are packed into an authenticated AES-256-GCM
container. Existing path-based calls continue to work because the runtime
resolves files from the pack when necessary.

Packing prevents accidental loose-file distribution and detects modified pack
entries. It is not DRM: a device that can run the game can ultimately access
the decrypted data.

## Release metadata

Each target writes `release.json` with the build version, filenames, sizes, and
SHA-256 hashes. Publish immutable versioned artifacts. If an update service
consumes the manifest, sign that manifest in the release pipeline.

The web target also creates a versioned service-worker cache. Change the game
version for a release so clients receive a new cache.

## Current web scope

The web backend supports the engine lifecycle, ECS, NumPy batch queries,
encrypted image assets, Canvas sprite batches, text, rectangles, keyboard, and
mouse state.

The 3D renderer, custom shaders, render textures, ImGui, gamepads, and complete
streaming audio are not yet equivalent to desktop. Unsupported APIs raise
clearly where possible; test the web build instead of assuming parity.

The generated page loads the configured Pyodide distribution from jsDelivr.
Vendor it beside the build if the game must start fully offline.

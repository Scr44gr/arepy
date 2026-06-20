# Game builder

Arepy ships an extensible builder with two targets:

- `windows`: a Nuitka one-file executable.
- `web`: a static Pyodide bundle with a Canvas 2D backend.

Install the optional build tools:

```bash
pip install "arepy[builder]"
```

Create `arepy.build.toml` next to the game entrypoint:

```toml
[build]
entrypoint = "main.py"
name = "my-game"
version = "1.0.0"
output_dir = "dist/my-game"
assets = ["assets"]
embed_assets = false
web_title = "My Game"
```

Then export one or both targets:

```bash
arepy --export windows web
```

The bunnymark example includes a ready-to-use configuration:

```bash
arepy --export windows web --config examples/bunnymark.build.toml
```

`python -m arepy` exposes the same interface. The previous `arepy-build`
command remains available as a compatibility alias.

## Assets

Every configured asset directory is packed into one authenticated
AES-256-GCM `.assets` container. Existing calls such as
`asset_store.load_texture(renderer, "player", "./assets/player.png")` keep
working.

On desktop, the encrypted pack is separate by default so asset-only releases
do not require replacing the executable. Set `embed_assets = true` for a
single-file build. Assets are extracted to a temporary runtime directory only
when a path-based backend requests them, and that directory is removed when
the game exits. On web, the browser decrypts the pack into Pyodide's in-memory
filesystem before importing the game.

This prevents shipping loose source assets and detects modified pack entries.
It is not DRM: a client which can run the game necessarily has access to the
decryption key and plaintext at runtime.

## Updates

Each target writes a `release.json` with the build version, filenames, sizes,
and SHA-256 hashes. Publish immutable versioned artifacts and sign the release
metadata in the update service. The manifest is intentionally transport
agnostic so a future TUF-compatible updater, itch.io pipeline, or custom CDN
can consume the same output.

The web target also generates a versioned service worker cache. Changing the
build version creates a new cache and removes older Arepy caches on activation.

## Web target scope

The first web backend supports the engine lifecycle, ECS, NumPy batch queries,
encrypted image assets, Canvas sprite batches, text, rectangles, keyboard, and
mouse state. The 3D renderer, custom shaders, render textures, ImGui, and full
WebAudio streaming are explicit extension points and currently raise
`NotImplementedError` when used.

The generated page loads Pyodide from jsDelivr. Vendor the selected Pyodide
distribution beside the build if fully offline deployment is required.

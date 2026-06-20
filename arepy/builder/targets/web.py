"""Pyodide and Canvas based web exporter."""

from __future__ import annotations

import json
import shutil
import zipfile
from pathlib import Path

from ..assets import AssetPack, build_asset_pack
from ..config import BuildConfig
from ..errors import BuilderError
from ..manifest import write_release_manifest
from ..models import BuildArtifact, BuildTarget

_EXCLUDED_SOURCE_PARTS = {
    ".git",
    ".venv",
    "build",
    "dist",
    "docs",
    "htmlcov",
    "site",
    "target",
    "tests",
    "venv",
    "__pycache__",
}


class WebTarget:
    """Generate a static web bundle running Arepy through Pyodide."""

    target = BuildTarget.WEB

    def build(self, config: BuildConfig) -> BuildArtifact:
        """Build a browser bundle and an update-ready file manifest."""

        target_dir = config.output_dir / "web"
        if target_dir.exists():
            shutil.rmtree(target_dir)
        target_dir.mkdir(parents=True)

        pack = build_asset_pack(
            config.assets,
            target_dir / f"{config.name}.assets",
            project_root=config.project_root,
        )
        source_zip = target_dir / "game.zip"
        _build_source_zip(config, source_zip)
        entry_module = _entry_module(config)

        (target_dir / "index.html").write_text(
            _index_html(
                title=config.web_title or config.name,
                pyodide_version=config.pyodide_version,
            ),
            encoding="utf-8",
        )
        (target_dir / "runtime.js").write_text(_runtime_javascript(), encoding="utf-8")
        (target_dir / "bootstrap.js").write_text(
            _bootstrap_javascript(config, pack, entry_module),
            encoding="utf-8",
        )
        (target_dir / "service-worker.js").write_text(
            _service_worker(config),
            encoding="utf-8",
        )

        files = [
            path
            for path in target_dir.iterdir()
            if path.is_file() and path.name != "release.json"
        ]
        manifest = write_release_manifest(
            target_dir / "release.json",
            name=config.name,
            version=config.version,
            target=self.target.value,
            files=files,
        )
        return BuildArtifact(self.target, target_dir / "index.html", manifest)


def _build_source_zip(config: BuildConfig, output: Path) -> None:
    arepy_root = Path(__file__).resolve().parents[2]
    written: set[str] = set()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for source in arepy_root.rglob("*.py"):
            if "builder" in source.relative_to(arepy_root).parts:
                continue
            arcname = (Path("arepy") / source.relative_to(arepy_root)).as_posix()
            archive.write(source, arcname)
            written.add(arcname)

        for source in config.project_root.rglob("*.py"):
            relative = source.relative_to(config.project_root)
            if any(part in _EXCLUDED_SOURCE_PARTS for part in relative.parts):
                continue
            if relative.parts and relative.parts[0] == "arepy":
                continue
            arcname = relative.as_posix()
            if arcname not in written:
                archive.write(source, arcname)
                written.add(arcname)

    expected = config.entrypoint.relative_to(config.project_root).as_posix()
    if expected not in written:
        raise BuilderError(f"Entrypoint was not included in web source bundle: {expected}")


def _entry_module(config: BuildConfig) -> str:
    relative = config.entrypoint.relative_to(config.project_root)
    parts = list(relative.with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _index_html(*, title: str, pyodide_version: str) -> str:
    safe_title = (
        title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{safe_title}</title>
  <style>
    html,body {{ margin:0; width:100%; height:100%; background:#11131a; color:#e9edf5; }}
    body {{ display:grid; place-items:center; font:14px system-ui,sans-serif; overflow:hidden; }}
    #shell {{ display:grid; gap:12px; justify-items:center; }}
    #arepy-canvas {{ background:#fff; max-width:100vw; max-height:calc(100vh - 42px); image-rendering:pixelated; }}
    #status {{ opacity:.8; min-height:20px; }}
    #status.error {{ color:#ff8e8e; white-space:pre-wrap; max-width:90vw; }}
  </style>
  <script src="https://cdn.jsdelivr.net/pyodide/v{pyodide_version}/full/pyodide.js"></script>
</head>
<body>
  <main id="shell">
    <canvas id="arepy-canvas" width="640" height="480"></canvas>
    <div id="status">Loading Arepy runtime…</div>
  </main>
  <script src="runtime.js"></script>
  <script src="bootstrap.js"></script>
</body>
</html>
"""


def _bootstrap_javascript(
    config: BuildConfig,
    pack: AssetPack,
    entry_module: str,
) -> str:
    settings = {
        "assetPack": pack.path.name,
        "assetKey": pack.encoded_key,
        "entryModule": entry_module,
        "pyodideIndex": (
            f"https://cdn.jsdelivr.net/pyodide/v{config.pyodide_version}/full/"
        ),
    }
    return (
        "globalThis.AREPY_BUILD = "
        + json.dumps(settings, separators=(",", ":"))
        + ";\narepyRuntime.start(globalThis.AREPY_BUILD);\n"
    )


def _runtime_javascript() -> str:
    return r"""(() => {
  const canvas = document.getElementById("arepy-canvas");
  const status = document.getElementById("status");
  const ctx = canvas.getContext("2d", { alpha: false });
  const images = new Map();
  const downKeys = new Set(), pressedKeys = new Set(), releasedKeys = new Set();
  const downMouse = new Set(), pressedMouse = new Set(), releasedMouse = new Set();
  let mouseX = 0, mouseY = 0, closed = false;
  let frameCount = 0, frameWindowStart = performance.now();

  const normalize = path => String(path).replaceAll("\\", "/").replace(/^\.?\//, "");
  const keyCode = event => event.key.length === 1 ? event.key.toUpperCase().charCodeAt(0) :
    ({Escape:256,Enter:257,Tab:258,Backspace:259,ArrowRight:262,ArrowLeft:263,
      ArrowDown:264,ArrowUp:265,Shift:340,Control:341,Alt:342," ":32}[event.key] ?? 0);
  addEventListener("keydown", event => { const code=keyCode(event); if(!downKeys.has(code)) pressedKeys.add(code); downKeys.add(code); });
  addEventListener("keyup", event => { const code=keyCode(event); downKeys.delete(code); releasedKeys.add(code); });
  canvas.addEventListener("pointerdown", event => { downMouse.add(event.button); pressedMouse.add(event.button); });
  addEventListener("pointerup", event => { downMouse.delete(event.button); releasedMouse.add(event.button); });
  canvas.addEventListener("pointermove", event => {
    const rect=canvas.getBoundingClientRect();
    mouseX=(event.clientX-rect.left)*canvas.width/rect.width;
    mouseY=(event.clientY-rect.top)*canvas.height/rect.height;
  });

  const b64 = value => Uint8Array.from(atob(value.replaceAll("-","+").replaceAll("_","/")), c => c.charCodeAt(0));
  const mimeFor = path => path.endsWith(".png") ? "image/png" : path.endsWith(".jpg") || path.endsWith(".jpeg") ? "image/jpeg" : path.endsWith(".webp") ? "image/webp" : "";
  const mkdirParent = (FS, path) => { const parts=path.split("/"); parts.pop(); let current=""; for(const part of parts){ current += `/${part}`; try{FS.mkdir(current)}catch{} } };

  async function loadAssets(pyodide, settings) {
    const bytes = new Uint8Array(await (await fetch(settings.assetPack)).arrayBuffer());
    const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
    const headerLength = view.getUint32(5, true);
    const payloadOffset = 9 + headerLength;
    const header = JSON.parse(new TextDecoder().decode(bytes.slice(9, payloadOffset)));
    const key = await crypto.subtle.importKey("raw", b64(settings.assetKey), "AES-GCM", false, ["decrypt"]);
    for (const entry of header.entries) {
      const encrypted = bytes.slice(payloadOffset + entry.offset, payloadOffset + entry.offset + entry.length);
      const plain = new Uint8Array(await crypto.subtle.decrypt({
        name:"AES-GCM", iv:b64(entry.nonce), additionalData:new TextEncoder().encode(entry.path)
      }, key, encrypted));
      const path = normalize(entry.path);
      mkdirParent(pyodide.FS, path);
      pyodide.FS.writeFile(`/${path}`, plain);
      const mime = mimeFor(path);
      if (mime) images.set(path, await createImageBitmap(new Blob([plain], {type:mime})));
    }
  }

  globalThis.arepyRuntime = {
    async start(settings) {
      try {
        status.textContent = "Loading Python and NumPy…";
        const pyodide = await loadPyodide({indexURL: settings.pyodideIndex});
        await pyodide.loadPackage("numpy");
        status.textContent = "Decrypting assets…";
        await loadAssets(pyodide, settings);
        pyodide.FS.writeFile("/game.zip", new Uint8Array(await (await fetch("game.zip")).arrayBuffer()));
        status.textContent = "Starting game…";
        await pyodide.runPythonAsync(`
import os, sys, importlib
os.environ["AREPY_PLATFORM"] = "web"
os.chdir("/")
sys.path.insert(0, "/game.zip")
module = importlib.import_module(${JSON.stringify(settings.entryModule)})
module.main()
`);
        status.textContent = "Running";
        if ("serviceWorker" in navigator) navigator.serviceWorker.register("./service-worker.js");
      } catch (error) {
        console.error(error);
        status.className = "error";
        status.textContent = String(error);
      }
    },
    createWindow(width,height,title){ canvas.width=width; canvas.height=height; document.title=title; ctx.imageSmoothingEnabled=false; canvas.focus(); },
    resize(width,height){ canvas.width=width; canvas.height=height; },
    width:()=>canvas.width, height:()=>canvas.height, close:()=>{closed=true}, shouldClose:()=>closed,
    focus:()=>canvas.focus(), toggleFullscreen:()=>canvas.requestFullscreen?.(),
    setOpacity:value=>canvas.style.opacity=value, devicePixelRatio:()=>devicePixelRatio,
    screenWidth:()=>screen.width, screenHeight:()=>screen.height,
    setClipboardText:text=>navigator.clipboard?.writeText(text),
    getImage:path=>images.get(normalize(path)),
    clear:color=>{ctx.save();ctx.fillStyle=color;ctx.fillRect(0,0,canvas.width,canvas.height);ctx.restore();},
    fillRect:(x,y,w,h,color)=>{ctx.save();ctx.fillStyle=color;ctx.fillRect(x,y,w,h);ctx.restore();},
    drawText:(text,x,y,size,color)=>{ctx.save();ctx.font=`${size}px monospace`;ctx.fillStyle=color;ctx.textBaseline="top";ctx.fillText(text,x,y);ctx.restore();},
    measureText:(text,size)=>{ctx.save();ctx.font=`${size}px monospace`;const width=ctx.measureText(text).width;ctx.restore();return width;},
    drawImage:(image,sx,sy,sw,sh,dx,dy,dw,dh,r,g,b,a)=>{ctx.save();ctx.globalAlpha=a/255;ctx.drawImage(image,sx,sy,sw,sh,dx,dy,dw,dh);ctx.restore();},
    drawImageEx:(image,sx,sy,sw,sh,dx,dy,dw,dh,ox,oy,rotation,a)=>{ctx.save();ctx.globalAlpha=a/255;ctx.translate(dx,dy);ctx.rotate(rotation*Math.PI/180);ctx.drawImage(image,sx,sy,sw,sh,-ox,-oy,dw,dh);ctx.restore();},
    drawBatchPacked(image, packedProxy, alphaByte) {
      const view=packedProxy.getBuffer("f32");
      try {
        if(!view.c_contiguous || view.ndim !== 2 || view.shape[1] !== 11) throw new Error("Invalid Arepy packed batch");
        const data=view.data, start=view.offset, count=view.shape[0], stride=11;
        ctx.save(); ctx.globalAlpha=alphaByte/255;
        for(let i=0, base=start;i<count;i++,base+=stride){
          const angle=data[base+10], dx=data[base+4], dy=data[base+5], ox=data[base+8], oy=data[base+9];
          if(angle===0) ctx.drawImage(image,data[base],data[base+1],data[base+2],data[base+3],dx-ox,dy-oy,data[base+6],data[base+7]);
          else { ctx.save();ctx.translate(dx,dy);ctx.rotate(angle*Math.PI/180);ctx.drawImage(image,data[base],data[base+1],data[base+2],data[base+3],-ox,-oy,data[base+6],data[base+7]);ctx.restore(); }
        }
        ctx.restore();
      } finally {
        view.release();
      }
    },
    finishFrame(){
      frameCount += 1;
      const now = performance.now(), elapsed = now - frameWindowStart;
      if(elapsed >= 1000) {
        status.textContent = `Running · ${Math.round(frameCount * 1000 / elapsed)} FPS`;
        frameCount = 0;
        frameWindowStart = now;
      }
    },
    hideCursor:()=>{canvas.style.cursor="none"},
    showCursor:()=>{canvas.style.cursor="default"},
    cursorHidden:()=>canvas.style.cursor==="none",
    beginClip:(x,y,width,height)=>{ctx.save();ctx.beginPath();ctx.rect(x,y,width,height);ctx.clip();},
    endClip:()=>ctx.restore(),
    keyPressed:code=>pressedKeys.has(code), keyDown:code=>downKeys.has(code), keyReleased:code=>releasedKeys.has(code),
    mousePressed:button=>pressedMouse.has(button), mouseDown:button=>downMouse.has(button), mouseReleased:button=>releasedMouse.has(button),
    mouseX:()=>mouseX, mouseY:()=>mouseY,
    finishInputFrame(){ pressedKeys.clear();releasedKeys.clear();pressedMouse.clear();releasedMouse.clear(); }
  };
})();"""


def _service_worker(config: BuildConfig) -> str:
    cache_name = f"arepy-{config.name}-{config.version}"
    return f"""const CACHE={cache_name!r};
const FILES=["./","./index.html","./runtime.js","./bootstrap.js","./game.zip","./{config.name}.assets","./release.json"];
self.addEventListener("install", event => event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(FILES))));
self.addEventListener("activate", event => event.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(key => key !== CACHE).map(key => caches.delete(key))))));
self.addEventListener("fetch", event => event.respondWith(caches.match(event.request).then(hit => hit || fetch(event.request))));
"""

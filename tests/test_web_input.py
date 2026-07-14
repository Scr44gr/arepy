import importlib.util
import sys
from pathlib import Path
from types import ModuleType


def test_web_input_frame_hooks_finish_exactly_one_frame_each(monkeypatch) -> None:
    calls: list[str] = []
    runtime = ModuleType("arepyRuntime")
    runtime.finishInputFrame = lambda: calls.append("finishInputFrame")
    js_module = ModuleType("js")
    js_module.arepyRuntime = runtime
    module_path = (
        Path(__file__).parents[1]
        / "arepy"
        / "engine"
        / "integrations"
        / "web"
        / "input_repository.py"
    )
    spec = importlib.util.spec_from_file_location(
        "_test_web_input_repository", module_path
    )
    assert spec is not None
    assert spec.loader is not None

    monkeypatch.setitem(sys.modules, "js", js_module)
    input_repository = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(input_repository)
    input_repository._finish_frame()
    input_repository.pool_events()

    assert calls == ["finishInputFrame", "finishInputFrame"]

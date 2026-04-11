from pathlib import Path
from types import SimpleNamespace

import pytest

from arepy.engine import ArepyShader as EngineArepyShader
from arepy.engine import ShaderUniformType as EngineShaderUniformType
from arepy.engine.integrations.raylib.renderer import renderer_2d as raylib_renderer_2d
from arepy.engine.renderer import ArepyShader, ArepyTexture, ShaderUniformType


class FakeFFI:
    def __init__(self) -> None:
        self.NULL = object()
        self.buffers: list[dict[str, object]] = []

    def new(self, ctype: str, values: object) -> dict[str, object]:
        if isinstance(values, tuple):
            values = list(values)
        elif not isinstance(values, list):
            values = [values]

        buffer = {"ctype": ctype, "values": values}
        self.buffers.append(buffer)
        return buffer


@pytest.fixture
def fake_shader_backend(monkeypatch: pytest.MonkeyPatch) -> dict[str, object]:
    calls: dict[str, object] = {
        "load_shader": [],
        "compile_shader": [],
        "unload_shader": [],
        "begin_shader_mode": [],
        "end_shader_mode": 0,
        "get_shader_location": [],
        "set_shader_value": [],
        "set_shader_value_texture": [],
        "set_shader_value_matrix": [],
    }
    fake_ffi = FakeFFI()
    next_location = {"value": 3}
    cached_locations: dict[str, int] = {}

    def load_shader(vertex_path: object, fragment_path: object) -> object:
        calls["load_shader"].append((vertex_path, fragment_path))
        return SimpleNamespace(id=17)

    def compile_shader(vertex_source: object, fragment_source: object) -> object:
        calls["compile_shader"].append((vertex_source, fragment_source))
        return SimpleNamespace(id=23)

    def unload_shader(shader_ref: object) -> None:
        calls["unload_shader"].append(shader_ref)

    def begin_shader_mode(shader_ref: object) -> None:
        calls["begin_shader_mode"].append(shader_ref)

    def end_shader_mode() -> None:
        calls["end_shader_mode"] += 1

    def get_shader_location(shader_ref: object, uniform_name: bytes) -> int:
        decoded_name = uniform_name.decode("utf-8")
        calls["get_shader_location"].append((shader_ref, decoded_name))
        if decoded_name == "missing_uniform":
            return -1
        if decoded_name not in cached_locations:
            cached_locations[decoded_name] = next_location["value"]
            next_location["value"] += 1
        return cached_locations[decoded_name]

    def set_shader_value(
        shader_ref: object,
        location: int,
        buffer: dict[str, object],
        uniform_type: int,
    ) -> None:
        calls["set_shader_value"].append(
            {
                "shader": shader_ref,
                "location": location,
                "buffer": buffer,
                "type": uniform_type,
            }
        )

    def set_shader_value_texture(
        shader_ref: object,
        location: int,
        texture_ref: object,
    ) -> None:
        calls["set_shader_value_texture"].append(
            {
                "shader": shader_ref,
                "location": location,
                "texture": texture_ref,
            }
        )

    def set_shader_value_matrix(
        shader_ref: object, location: int, matrix: object
    ) -> None:
        calls["set_shader_value_matrix"].append(
            {
                "shader": shader_ref,
                "location": location,
                "matrix": matrix,
            }
        )

    monkeypatch.setattr(raylib_renderer_2d.rl, "LoadShader", load_shader)
    monkeypatch.setattr(raylib_renderer_2d.rl, "LoadShaderFromMemory", compile_shader)
    monkeypatch.setattr(raylib_renderer_2d.rl, "UnloadShader", unload_shader)
    monkeypatch.setattr(raylib_renderer_2d.rl, "BeginShaderMode", begin_shader_mode)
    monkeypatch.setattr(raylib_renderer_2d.rl, "EndShaderMode", end_shader_mode)
    monkeypatch.setattr(raylib_renderer_2d.rl, "GetShaderLocation", get_shader_location)
    monkeypatch.setattr(raylib_renderer_2d.rl, "SetShaderValue", set_shader_value)
    monkeypatch.setattr(
        raylib_renderer_2d.rl,
        "SetShaderValueTexture",
        set_shader_value_texture,
    )
    monkeypatch.setattr(
        raylib_renderer_2d.rl,
        "SetShaderValueMatrix",
        set_shader_value_matrix,
    )
    monkeypatch.setattr(raylib_renderer_2d.rl, "ffi", fake_ffi, raising=False)
    monkeypatch.setattr(
        raylib_renderer_2d, "rlMatrix", lambda *values: ("matrix", values)
    )

    calls["ffi"] = fake_ffi
    return calls


def make_shader(shader_id: int = 99) -> ArepyShader:
    shader = ArepyShader(shader_id)
    shader._ref_shader = SimpleNamespace(id=shader_id)
    return shader


def test_shader_symbols_are_exported_from_engine() -> None:
    assert EngineArepyShader is ArepyShader
    assert EngineShaderUniformType is ShaderUniformType


def test_load_shader_wraps_backend_handle(
    fake_shader_backend: dict[str, object],
) -> None:
    shader = raylib_renderer_2d.load_shader(Path("basic.vs"), Path("basic.fs"))

    assert isinstance(shader, ArepyShader)
    assert shader.shader_id == 17
    assert fake_shader_backend["load_shader"] == [(b"basic.vs", b"basic.fs")]


def test_compile_shader_requires_at_least_one_stage() -> None:
    with pytest.raises(ValueError):
        raylib_renderer_2d.compile_shader()

    with pytest.raises(ValueError):
        raylib_renderer_2d.load_shader()


def test_begin_and_end_shader_mode(fake_shader_backend: dict[str, object]) -> None:
    shader = make_shader()

    raylib_renderer_2d.begin_shader_mode(shader)
    raylib_renderer_2d.end_shader_mode()

    assert fake_shader_backend["begin_shader_mode"] == [shader._ref_shader]
    assert fake_shader_backend["end_shader_mode"] == 1


def test_unload_shader_clears_cached_locations(
    fake_shader_backend: dict[str, object],
) -> None:
    shader = make_shader(7)
    shader._uniform_locations["u_color"] = 12
    shader_ref = shader._ref_shader

    raylib_renderer_2d.unload_shader(shader)

    assert fake_shader_backend["unload_shader"] == [shader_ref]
    assert shader._uniform_locations == {}
    assert shader._ref_shader is None


def test_set_shader_value_caches_uniform_locations(
    fake_shader_backend: dict[str, object],
) -> None:
    shader = make_shader()

    raylib_renderer_2d.set_shader_value(
        shader,
        ShaderUniformType.VEC4,
        "u_color",
        (1.0, 0.5, 0.25, 1.0),
    )
    raylib_renderer_2d.set_shader_value(
        shader,
        ShaderUniformType.VEC4,
        "u_color",
        [0.1, 0.2, 0.3, 0.4],
    )

    assert fake_shader_backend["get_shader_location"] == [
        (shader._ref_shader, "u_color")
    ]

    first_call = fake_shader_backend["set_shader_value"][0]
    second_call = fake_shader_backend["set_shader_value"][1]
    assert first_call["location"] == second_call["location"] == 3
    assert first_call["type"] == raylib_renderer_2d.rl.SHADER_UNIFORM_VEC4
    assert first_call["buffer"] == {
        "ctype": "float[4]",
        "values": [1.0, 0.5, 0.25, 1.0],
    }
    assert second_call["buffer"] == {
        "ctype": "float[4]",
        "values": [0.1, 0.2, 0.3, 0.4],
    }


def test_set_shader_value_supports_sampler2d(
    fake_shader_backend: dict[str, object],
) -> None:
    shader = make_shader()
    texture = ArepyTexture(5, (64, 64))
    texture._ref_texture = SimpleNamespace(id=77)

    raylib_renderer_2d.set_shader_value(
        shader,
        ShaderUniformType.SAMPLER2D,
        "u_texture",
        texture,
    )

    assert fake_shader_backend["set_shader_value_texture"] == [
        {
            "shader": shader._ref_shader,
            "location": 3,
            "texture": texture._ref_texture,
        }
    ]


def test_set_shader_value_supports_mat4(fake_shader_backend: dict[str, object]) -> None:
    shader = make_shader()
    matrix = [float(index) for index in range(16)]

    raylib_renderer_2d.set_shader_value(
        shader,
        ShaderUniformType.MAT4,
        "u_transform",
        matrix,
    )

    assert fake_shader_backend["set_shader_value_matrix"] == [
        {
            "shader": shader._ref_shader,
            "location": 3,
            "matrix": ("matrix", tuple(matrix)),
        }
    ]


def test_set_shader_value_validates_shape_and_type(
    fake_shader_backend: dict[str, object],
) -> None:
    shader = make_shader()

    with pytest.raises(ValueError):
        raylib_renderer_2d.set_shader_value(
            shader,
            ShaderUniformType.VEC3,
            "u_offset",
            (1.0, 2.0),
        )

    with pytest.raises(TypeError):
        raylib_renderer_2d.set_shader_value(
            shader,
            ShaderUniformType.SAMPLER2D,
            "u_texture",
            1,
        )

    with pytest.raises(ValueError):
        raylib_renderer_2d.set_shader_value(
            shader,
            ShaderUniformType.FLOAT,
            "missing_uniform",
            1.0,
        )


def test_unload_texture_handles_standard_textures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[object] = []
    texture = ArepyTexture(1, (32, 32))
    texture._ref_texture = SimpleNamespace(id=41)
    texture_ref = texture._ref_texture

    monkeypatch.setattr(
        raylib_renderer_2d.rl, "UnloadTexture", lambda ref: calls.append(ref)
    )

    raylib_renderer_2d.unload_texture(texture)

    assert calls == [texture_ref]
    assert texture._ref_texture is None


def test_unload_texture_handles_render_textures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    unload_texture_calls: list[object] = []
    unload_render_texture_calls: list[object] = []
    texture = ArepyTexture(2, (64, 64))
    texture._ref_texture = SimpleNamespace(id=51)
    texture._ref_render_texture = SimpleNamespace(id=52)

    monkeypatch.setattr(
        raylib_renderer_2d.rl,
        "UnloadTexture",
        lambda ref: unload_texture_calls.append(ref),
    )
    monkeypatch.setattr(
        raylib_renderer_2d.rl,
        "UnloadRenderTexture",
        lambda ref: unload_render_texture_calls.append(ref),
    )

    render_texture_ref = texture._ref_render_texture

    raylib_renderer_2d.unload_texture(texture)

    assert unload_render_texture_calls == [render_texture_ref]
    assert unload_texture_calls == []
    assert texture._ref_texture is None
    assert texture._ref_render_texture is None

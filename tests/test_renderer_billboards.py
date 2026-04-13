from types import SimpleNamespace

import pytest

from arepy.bundle.components.camera import Camera3D
from arepy.engine.integrations.raylib.renderer import renderer_3d as raylib_renderer_3d
from arepy.engine.renderer import ArepyTexture, Color, Rect
from arepy.math import Vec2, Vec3


@pytest.fixture
def fake_billboard_backend(monkeypatch: pytest.MonkeyPatch) -> dict[str, list[object]]:
    calls: dict[str, list[object]] = {
        "draw_billboard": [],
        "draw_billboard_rec": [],
        "disable_depth_mask": [],
        "enable_depth_mask": [],
    }

    monkeypatch.setattr(raylib_renderer_3d, "_cameras", [])
    monkeypatch.setattr(raylib_renderer_3d, "_current_camera", None)

    def draw_billboard(
        camera_ref: object,
        texture_ref: object,
        position: tuple[float, float, float],
        size: float,
        tint: tuple[int, int, int, int],
    ) -> None:
        calls["draw_billboard"].append(
            {
                "camera": camera_ref,
                "texture": texture_ref,
                "position": position,
                "size": size,
                "tint": tint,
            }
        )

    def draw_billboard_rec(
        camera_ref: object,
        texture_ref: object,
        source: tuple[float, float, int, int],
        position: tuple[float, float, float],
        size: tuple[float, float],
        tint: tuple[int, int, int, int],
    ) -> None:
        calls["draw_billboard_rec"].append(
            {
                "camera": camera_ref,
                "texture": texture_ref,
                "source": source,
                "position": position,
                "size": size,
                "tint": tint,
            }
        )

    def disable_depth_mask() -> None:
        calls["disable_depth_mask"].append(True)

    def enable_depth_mask() -> None:
        calls["enable_depth_mask"].append(True)

    monkeypatch.setattr(raylib_renderer_3d.rl, "DrawBillboard", draw_billboard)
    monkeypatch.setattr(raylib_renderer_3d.rl, "DrawBillboardRec", draw_billboard_rec)
    monkeypatch.setattr(raylib_renderer_3d.rl, "rlDisableDepthMask", disable_depth_mask)
    monkeypatch.setattr(raylib_renderer_3d.rl, "rlEnableDepthMask", enable_depth_mask)
    return calls


def make_texture(texture_id: int = 7) -> ArepyTexture:
    texture = ArepyTexture(texture_id, (32, 32))
    texture._ref_texture = SimpleNamespace(id=texture_id)
    return texture


def make_camera(camera_id: int = 11) -> Camera3D:
    camera = Camera3D()
    camera._ref = SimpleNamespace(id=camera_id)
    return camera


def test_draw_billboard_uses_current_camera_and_texture(
    monkeypatch: pytest.MonkeyPatch,
    fake_billboard_backend: dict[str, list[object]],
) -> None:
    camera = make_camera()
    texture = make_texture()

    monkeypatch.setattr(raylib_renderer_3d, "_current_camera", camera)

    raylib_renderer_3d.draw_billboard(
        texture,
        Vec3(1.0, 2.0, 3.0),
        1.5,
        Color(255, 200, 150, 255),
    )

    assert fake_billboard_backend["draw_billboard"] == [
        {
            "camera": camera._ref,
            "texture": texture._ref_texture,
            "position": (1.0, 2.0, 3.0),
            "size": 1.5,
            "tint": (255, 200, 150, 255),
        }
    ]
    assert fake_billboard_backend["disable_depth_mask"] == [True]
    assert fake_billboard_backend["enable_depth_mask"] == [True]


def test_draw_billboard_rec_uses_source_rect(
    monkeypatch: pytest.MonkeyPatch,
    fake_billboard_backend: dict[str, list[object]],
) -> None:
    camera = make_camera()
    texture = make_texture()

    monkeypatch.setattr(raylib_renderer_3d, "_current_camera", camera)

    raylib_renderer_3d.draw_billboard_rec(
        texture,
        Rect(0.0, 0.0, 32, 32),
        Vec3(-2.0, 0.5, 4.0),
        Vec2(1.25, 1.75),
        Color(255, 255, 255, 255),
    )

    assert fake_billboard_backend["draw_billboard_rec"] == [
        {
            "camera": camera._ref,
            "texture": texture._ref_texture,
            "source": (0.0, 0.0, 32, 32),
            "position": (-2.0, 0.5, 4.0),
            "size": (1.25, 1.75),
            "tint": (255, 255, 255, 255),
        }
    ]
    assert fake_billboard_backend["disable_depth_mask"] == [True]
    assert fake_billboard_backend["enable_depth_mask"] == [True]


def test_draw_billboard_requires_active_camera(
    fake_billboard_backend: dict[str, list[object]],
) -> None:
    texture = make_texture()

    with pytest.raises(RuntimeError, match="No current camera set"):
        raylib_renderer_3d.draw_billboard(
            texture,
            Vec3(0.0, 1.0, 0.0),
            1.0,
            Color(255, 255, 255, 255),
        )


def test_draw_billboard_requires_loaded_texture(
    monkeypatch: pytest.MonkeyPatch,
    fake_billboard_backend: dict[str, list[object]],
) -> None:
    camera = make_camera()
    texture = ArepyTexture(3, (32, 32))

    monkeypatch.setattr(raylib_renderer_3d, "_current_camera", camera)

    with pytest.raises(ValueError, match="Texture must be loaded"):
        raylib_renderer_3d.draw_billboard(
            texture,
            Vec3(0.0, 1.0, 0.0),
            1.0,
            Color(255, 255, 255, 255),
        )
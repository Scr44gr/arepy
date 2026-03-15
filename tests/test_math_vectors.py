import math

from arepy.bundle.components.transform import Transform
from arepy.math import Vec2, Vec3


def test_vec2_supports_scalar_multiplication_on_both_sides():
    vector = Vec2(2, 3)

    assert vector * 2 == Vec2(4, 6)
    assert 2 * vector == Vec2(4, 6)


def test_vec2_in_place_operations_preserve_current_usage_style():
    vector = Vec2(1, 2)

    vector += Vec2(3, 4)
    vector *= 2
    vector /= 4

    assert vector == Vec2(2, 3)


def test_vec2_normalize_zero_is_safe():
    vector = Vec2(0, 0)

    assert vector.normalize() == Vec2(0, 0)
    vector.normalize_ip()

    assert vector == Vec2(0, 0)


def test_vec3_supports_scalar_multiplication_on_both_sides():
    vector = Vec3(2, 3, 4)

    assert vector * 2 == Vec3(4, 6, 8)
    assert 2 * vector == Vec3(4, 6, 8)


def test_vec3_in_place_operations_preserve_current_usage_style():
    vector = Vec3(1, 2, 3)

    vector += Vec3(3, 4, 5)
    vector *= 2
    vector /= 4

    assert vector == Vec3(2, 3, 4)


def test_vec3_normalize_zero_is_safe():
    assert Vec3(0, 0, 0).normalize() == Vec3(0, 0, 0)


def test_vec3_normalize_ip_zero_is_safe():
    vector = Vec3(0, 0, 0)

    vector.normalize_ip()

    assert vector == Vec3(0, 0, 0)


def test_vec3_scale_ip_matches_scalar_multiplication():
    vector = Vec3(2, 3, 4)

    vector.scale_ip(0.5)

    assert vector == Vec3(1, 1.5, 2)


def test_vec3_angle_zero_vector_is_safe():
    assert Vec3(0, 0, 0).angle(Vec3(1, 0, 0)) == 0.0


def test_vec3_angle_clamps_floating_point_drift():
    angle = Vec3(1, 0, 0).angle(Vec3(1, 0, 0))

    assert math.isclose(angle, 0.0)


def test_vec3_project_zero_vector_target_is_safe():
    assert Vec3(1, 2, 3).project(Vec3(0, 0, 0)) == Vec3(0, 0, 0)


def test_transform_default_vectors_are_not_shared_between_instances():
    transform_a = Transform()
    transform_b = Transform()

    transform_a.position.x = 10
    transform_a.scale.y = 99
    transform_a.origin.x = 7

    assert transform_b.position == Vec2(0, 0)
    assert transform_b.scale == Vec2(1, 1)
    assert transform_b.origin == Vec2(0, 0)

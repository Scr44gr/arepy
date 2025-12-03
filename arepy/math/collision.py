from arepy.engine.renderer import Rect


def check_collision_point_rec(point: tuple[float, float], rect: Rect) -> bool:
    return (
        point[0] >= rect.x
        and point[0] <= rect.x + rect.width
        and point[1] >= rect.y
        and point[1] <= rect.y + rect.height
    )

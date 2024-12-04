from enum import Enum
from typing import Callable

System = Callable[..., None]


class SystemPipeline(Enum):
    """Pipeline for systems to be executed in."""

    ASYNC_UPDATE = 4
    UPDATE = 0
    RENDER = 1
    INPUT = 2
    PHYSICS = 3

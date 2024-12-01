from enum import Enum
from typing import Callable

System = Callable[[], None]


class SystemPipeline(Enum):
    """Pipeline for systems to be executed in."""

    UPDATE = 0
    RENDER = 1
    INPUT = 2
    PHYSICS = 3

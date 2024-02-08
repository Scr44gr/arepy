from abc import ABC, abstractmethod


class BaseRenderer(ABC):
    @abstractmethod
    def render(self, *args, **kwargs):
        pass

    @abstractmethod
    def clear(self, *args, **kwargs):
        pass

from dataclasses import dataclass, field
from typing import Optional
import numpy as np
from glm import vec4

@dataclass
cdef class RendererData:
    index_data: np.ndarray
    index_count: int = 0
    texture_vbo: Optional[int] = None
    texture_vao: Optional[int] = None
    texture_ibo: Optional[int] = None
    quads_buffer: Optional[np.ndarray] = None
    quads_buffer_index: Optional[int] = None
    quad_vertex_positions: list = field(default_factory=lambda: [
        vec4(-0.5, 0.5, 0.0, 1.0),
        vec4(0.5, 0.5, 0.0, 1.0),
        vec4(0.5, -0.5, 0.0, 1.0),
        vec4(-0.5, -0.5, 0.0, 1.0),
    ])
    white_texture: int = 0
    white_texture_slot: int = 0
    texture_slots: list = field(default_factory=lambda: [0] * 32)
    texture_slot_index: int = 1
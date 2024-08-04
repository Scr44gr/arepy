# type: ignore
from cython cimport boundscheck, wraparound
import numpy as np
cimport numpy as np

cdef class RendererData:
    cdef public np.ndarray index_data
    cdef public int index_count
    cdef public int texture_vbo
    cdef public int texture_vao
    cdef public int texture_ibo
    cdef public np.ndarray quads_buffer
    cdef public int quads_buffer_index
    cdef public int white_texture
    cdef public int white_texture_slot
    cdef public list texture_slots
    cdef public int texture_slot_index

    def __init__(self, int texture_vbo, int texture_vao, int texture_ibo, np.ndarray index_data, np.ndarray quads_buffer , int quads_buffer_index):
        self.quads_buffer = quads_buffer
        self.texture_vbo = texture_vbo
        self.texture_vao = texture_vao
        self.texture_ibo = texture_ibo
        self.index_data = index_data
        self.quads_buffer_index = quads_buffer_index
        self.white_texture_slot = 0
        self.texture_slots = [0] * 32
        self.texture_slot_index = 1
    
    # deallocate memory
    def __dealloc__(self):
        del self.index_data
        del self.quads_buffer




@boundscheck(False) #type: ignore
@wraparound(False)
cpdef bint is_outside_screen(
    tuple[float, float] rectangle_position,
    tuple[float, float] rectangle_size,
    tuple[float, float] screen_size,
):
    cdef float x, y, width, height, screen_width, screen_height
    x, y = rectangle_position
    width, height = rectangle_size
    screen_width, screen_height = screen_size
    return x + width < 0 or x > screen_width or y + height < 0 or y > screen_height #type: ignore

@boundscheck(False) #type: ignore
@wraparound(False)
cpdef tuple[float, float, float, float, float, float, float, float] get_texture_coordinates(
    tuple[float, float, float, float] src_rect,
    tuple[float, float, float, float] src_dest,
):
    cdef float texture_width, texture_height, w, h, x, y
    texture_width, texture_height = src_dest[0], src_dest[1]
    w, h, x, y = src_rect
    return (
        x / texture_width,
        (y + h) / texture_height,
        (x + w) / texture_width,
        (y + h) / texture_height,
        (x + w) / texture_width,
        y / texture_height,
        x / texture_width,
        y / texture_height,
    )

QUAD_VERTEX_POSITIONS = np.array(
    [
        [-0.5, 0.5, 0.0, 1.0],
        [0.5, 0.5, 0.0, 1.0],
        [0.5, -0.5, 0.0, 1.0],
        [-0.5, -0.5, 0.0, 1.0],
    ],
    dtype=np.float32,
)

cdef list[int] vertex_range = list(range(4))

@boundscheck(False) #type: ignore
@wraparound(False)
cpdef set_vertex_data(np.ndarray raw_vertices, RendererData renderer_data):

    assert renderer_data.quads_buffer_index is not None
    cdef int current_quad_buffer_index
    for raw_vertex in raw_vertices:
        for _ in vertex_range:
            current_quad_buffer_index = renderer_data.quads_buffer_index
            renderer_data.quads_buffer[current_quad_buffer_index] = raw_vertex
            renderer_data.quads_buffer_index += 1
        renderer_data.index_count += 6

@boundscheck(False) #type: ignore
@wraparound(False)
cpdef update_vertex_transforms(np.ndarray raw_vertices, RendererData renderer_data):
    assert renderer_data.quads_buffer_index is not None
    cdef int current_quad_buffer_index
    renderer_data.quads_buffer_index = 0
    for raw_vertex in raw_vertices:
        for _ in vertex_range:
            current_quad_buffer_index = renderer_data.quads_buffer_index
            renderer_data.quads_buffer[current_quad_buffer_index] = raw_vertex
            renderer_data.quads_buffer_index += 1

def enable_renderdoc():
    """Enable RenderDoc."""
    import ctypes

    try:
        renderdoc = ctypes.cdll.LoadLibrary(
            r"C:\Program Files\RenderDoc\renderdoc.dll"
        )  # Windows

        if renderdoc:
            renderdoc.RDCInitGlobalHook.argtypes = [ctypes.c_char_p]
            renderdoc.RDCInitGlobalHook.restype = ctypes.c_bool
            renderdoc.RDCInitGlobalHook(None)
    except:
        pass

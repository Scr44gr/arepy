//! Native rendering helpers for Arepy's texture-atlas drawing path.

use numpy::PyReadonlyArray1;
use pyo3::exceptions::{PyRuntimeError, PyValueError};
use pyo3::prelude::*;
use std::mem;
use std::sync::OnceLock;

#[repr(C)]
#[derive(Clone, Copy)]
struct Texture {
    id: u32,
    width: i32,
    height: i32,
    mipmaps: i32,
    format: i32,
}

#[repr(C)]
#[derive(Clone, Copy)]
struct Rectangle {
    x: f32,
    y: f32,
    width: f32,
    height: f32,
}

#[repr(C)]
#[derive(Clone, Copy)]
struct Vector2 {
    x: f32,
    y: f32,
}

#[repr(C)]
#[derive(Clone, Copy)]
struct Color {
    r: u8,
    g: u8,
    b: u8,
    a: u8,
}

type DrawTextureRecFn = unsafe extern "C" fn(Texture, Rectangle, Vector2, Color);
type DrawRenderBatchActiveFn = unsafe extern "C" fn();

#[derive(Clone, Copy)]
struct RenderBackendFns {
    draw_texture_rec: DrawTextureRecFn,
    draw_render_batch_active: DrawRenderBatchActiveFn,
}

static RENDER_BACKEND_FNS: OnceLock<RenderBackendFns> = OnceLock::new();

#[pyfunction]
fn configure_render_backend(
    draw_texture_rec_addr: usize,
    draw_render_batch_active_addr: usize,
) -> PyResult<()> {
    if draw_texture_rec_addr == 0 || draw_render_batch_active_addr == 0 {
        return Err(PyValueError::new_err(
            "Render backend function pointers must be non-zero.",
        ));
    }

    let fns = RenderBackendFns {
        // SAFETY: Python passes raw function pointers resolved from the live render backend.
        draw_texture_rec: unsafe {
            mem::transmute::<usize, DrawTextureRecFn>(draw_texture_rec_addr)
        },
        // SAFETY: Python passes raw function pointers resolved from the live render backend.
        draw_render_batch_active: unsafe {
            mem::transmute::<usize, DrawRenderBatchActiveFn>(draw_render_batch_active_addr)
        },
    };

    let _ = RENDER_BACKEND_FNS.set(fns);
    Ok(())
}

#[pyfunction]
#[expect(
    clippy::too_many_arguments,
    reason = "PyO3 entry point mirrors Python-owned NumPy views without reshaping or copying."
)]
fn draw_texture_batch(
    texture_id: u32,
    texture_width: i32,
    texture_height: i32,
    texture_mipmaps: i32,
    texture_format: i32,
    entity_indices: PyReadonlyArray1<'_, i64>,
    src_x: PyReadonlyArray1<'_, f32>,
    src_y: PyReadonlyArray1<'_, f32>,
    src_width: PyReadonlyArray1<'_, f32>,
    src_height: PyReadonlyArray1<'_, f32>,
    position_x: PyReadonlyArray1<'_, f64>,
    position_y: PyReadonlyArray1<'_, f64>,
    color_rgba: (u8, u8, u8, u8),
) -> PyResult<()> {
    let fns = render_backend_fns()?;

    let entity_indices = entity_indices.as_slice()?;
    let src_x = src_x.as_slice()?;
    let src_y = src_y.as_slice()?;
    let src_width = src_width.as_slice()?;
    let src_height = src_height.as_slice()?;
    let position_x = position_x.as_slice()?;
    let position_y = position_y.as_slice()?;

    let batch_len = entity_indices.len();
    if src_x.len() != batch_len
        || src_y.len() != batch_len
        || src_width.len() != batch_len
        || src_height.len() != batch_len
    {
        return Err(PyValueError::new_err(
            "All source arrays and entity_indices must have the same length.",
        ));
    }
    if position_x.len() != position_y.len() {
        return Err(PyValueError::new_err(
            "position_x and position_y must have the same length.",
        ));
    }

    let texture = Texture {
        id: texture_id,
        width: texture_width,
        height: texture_height,
        mipmaps: texture_mipmaps,
        format: texture_format,
    };
    let color = Color {
        r: color_rgba.0,
        g: color_rgba.1,
        b: color_rgba.2,
        a: color_rgba.3,
    };

    // SAFETY: the function pointer comes from `configure_render_backend` and is expected
    // to remain valid for the lifetime of the loaded render backend.
    unsafe {
        (fns.draw_render_batch_active)();
    }

    for index in 0..batch_len {
        let entity_index = usize::try_from(entity_indices[index]).map_err(|_| {
            PyValueError::new_err("Texture batch entity indices must be non-negative.")
        })?;
        if entity_index >= position_x.len() {
            return Err(PyValueError::new_err(
                "Texture batch entity index is out of range for the provided position views.",
            ));
        }

        let source = Rectangle {
            x: src_x[index],
            y: src_y[index],
            width: src_width[index],
            height: src_height[index],
        };
        let position = Vector2 {
            x: position_x[entity_index] as f32,
            y: position_y[entity_index] as f32,
        };

        // SAFETY: the function pointer comes from `configure_render_backend`, and the
        // copied POD structs match raylib's C ABI for this call.
        unsafe {
            (fns.draw_texture_rec)(texture, source, position, color);
        }
    }

    Ok(())
}

fn render_backend_fns() -> PyResult<RenderBackendFns> {
    RENDER_BACKEND_FNS.get().copied().ok_or_else(|| {
        PyRuntimeError::new_err("Render backend function pointers have not been configured.")
    })
}

#[pymodule]
fn arepy_renderer(_py: Python<'_>, module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add_function(wrap_pyfunction!(configure_render_backend, module)?)?;
    module.add_function(wrap_pyfunction!(draw_texture_batch, module)?)?;
    Ok(())
}

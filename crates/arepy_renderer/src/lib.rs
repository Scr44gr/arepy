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

type DrawTextureProFn = unsafe extern "C" fn(Texture, Rectangle, Rectangle, Vector2, f32, Color);

#[derive(Clone, Copy)]
struct RenderBackendFns {
    draw_texture_pro: DrawTextureProFn,
}

static RENDER_BACKEND_FNS: OnceLock<RenderBackendFns> = OnceLock::new();

#[pyfunction]
fn configure_render_backend(draw_texture_pro_addr: usize) -> PyResult<()> {
    if draw_texture_pro_addr == 0 {
        return Err(PyValueError::new_err(
            "Render backend function pointers must be non-zero.",
        ));
    }

    let fns = RenderBackendFns {
        // SAFETY: Python passes raw function pointers resolved from the live render backend.
        draw_texture_pro: unsafe {
            mem::transmute::<usize, DrawTextureProFn>(draw_texture_pro_addr)
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
    dest_x: PyReadonlyArray1<'_, f64>,
    dest_y: PyReadonlyArray1<'_, f64>,
    dest_width: PyReadonlyArray1<'_, f64>,
    dest_height: PyReadonlyArray1<'_, f64>,
    origin_x: PyReadonlyArray1<'_, f64>,
    origin_y: PyReadonlyArray1<'_, f64>,
    rotation: PyReadonlyArray1<'_, f64>,
    color_rgba: (u8, u8, u8, u8),
) -> PyResult<()> {
    let fns = render_backend_fns()?;

    let entity_indices = entity_indices.as_slice()?;
    let src_x = src_x.as_slice()?;
    let src_y = src_y.as_slice()?;
    let src_width = src_width.as_slice()?;
    let src_height = src_height.as_slice()?;
    let dest_x = dest_x.as_slice()?;
    let dest_y = dest_y.as_slice()?;
    let dest_width = dest_width.as_slice()?;
    let dest_height = dest_height.as_slice()?;
    let origin_x = origin_x.as_slice()?;
    let origin_y = origin_y.as_slice()?;
    let rotation = rotation.as_slice()?;

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
    if dest_x.len() != dest_y.len()
        || dest_x.len() != dest_width.len()
        || dest_x.len() != dest_height.len()
        || dest_x.len() != origin_x.len()
        || dest_x.len() != origin_y.len()
        || dest_x.len() != rotation.len()
    {
        return Err(PyValueError::new_err(
            "Destination, origin, and rotation arrays must have the same length.",
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

    for index in 0..batch_len {
        let entity_index = usize::try_from(entity_indices[index]).map_err(|_| {
            PyValueError::new_err("Texture batch entity indices must be non-negative.")
        })?;
        if entity_index >= dest_x.len() {
            return Err(PyValueError::new_err(
                "Texture batch entity index is out of range for the provided DrawTexturePro views.",
            ));
        }

        let source = Rectangle {
            x: src_x[index],
            y: src_y[index],
            width: src_width[index],
            height: src_height[index],
        };
        let dest = Rectangle {
            x: dest_x[entity_index] as f32,
            y: dest_y[entity_index] as f32,
            width: dest_width[entity_index] as f32,
            height: dest_height[entity_index] as f32,
        };
        let origin = Vector2 {
            x: origin_x[entity_index] as f32,
            y: origin_y[entity_index] as f32,
        };

        // SAFETY: the function pointer comes from `configure_render_backend`, and the
        // copied POD structs match raylib's C ABI for this call.
        unsafe {
            (fns.draw_texture_pro)(
                texture,
                source,
                dest,
                origin,
                rotation[entity_index] as f32,
                color,
            );
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

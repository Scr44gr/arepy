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
    draw_texture_pro_addr: usize,
}

static RENDER_BACKEND_FNS: OnceLock<RenderBackendFns> = OnceLock::new();

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum BackendConfigurationError {
    AddressMismatch,
}

fn configure_backend_once(
    storage: &OnceLock<RenderBackendFns>,
    backend: RenderBackendFns,
) -> Result<(), BackendConfigurationError> {
    let configured = storage.get_or_init(|| backend);
    if configured.draw_texture_pro_addr == backend.draw_texture_pro_addr {
        Ok(())
    } else {
        Err(BackendConfigurationError::AddressMismatch)
    }
}

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
        draw_texture_pro_addr,
    };

    configure_backend_once(&RENDER_BACKEND_FNS, fns).map_err(|_| {
        PyRuntimeError::new_err(
            "Render backend function pointers have already been configured with different addresses.",
        )
    })
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum BatchValidationError {
    SourceArrayLength,
    DrawViewLength,
    NegativeEntityIndex,
    EntityIndexOutOfRange,
}

fn validate_batch_inputs(
    entity_indices: &[i64],
    source_lengths: [usize; 4],
    draw_view_lengths: [usize; 7],
) -> Result<(), BatchValidationError> {
    let batch_len = entity_indices.len();
    if source_lengths.iter().any(|&length| length != batch_len) {
        return Err(BatchValidationError::SourceArrayLength);
    }

    let entity_count = draw_view_lengths[0];
    if draw_view_lengths[1..]
        .iter()
        .any(|&length| length != entity_count)
    {
        return Err(BatchValidationError::DrawViewLength);
    }

    for &raw_entity_index in entity_indices {
        if raw_entity_index < 0 {
            return Err(BatchValidationError::NegativeEntityIndex);
        }

        let entity_index = usize::try_from(raw_entity_index)
            .map_err(|_| BatchValidationError::EntityIndexOutOfRange)?;
        if entity_index >= entity_count {
            return Err(BatchValidationError::EntityIndexOutOfRange);
        }
    }

    Ok(())
}

fn batch_validation_py_error(error: BatchValidationError) -> PyErr {
    let message = match error {
        BatchValidationError::SourceArrayLength => {
            "All source arrays and entity_indices must have the same length."
        }
        BatchValidationError::DrawViewLength => {
            "Destination, origin, and rotation arrays must have the same length."
        }
        BatchValidationError::NegativeEntityIndex => {
            "Texture batch entity indices must be non-negative."
        }
        BatchValidationError::EntityIndexOutOfRange => {
            "Texture batch entity index is out of range for the provided DrawTexturePro views."
        }
    };
    PyValueError::new_err(message)
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

    validate_batch_inputs(
        entity_indices,
        [src_x.len(), src_y.len(), src_width.len(), src_height.len()],
        [
            dest_x.len(),
            dest_y.len(),
            dest_width.len(),
            dest_height.len(),
            origin_x.len(),
            origin_y.len(),
            rotation.len(),
        ],
    )
    .map_err(batch_validation_py_error)?;

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

    for (index, &raw_entity_index) in entity_indices.iter().enumerate() {
        let entity_index = raw_entity_index as usize;

        // SAFETY: `validate_batch_inputs` established that every source array contains
        // `index`, every draw view contains `entity_index`, and the signed-to-unsigned
        // conversion cannot truncate. The configured function pointer remains the only
        // external trust boundary, and these copied POD structs match raylib's C ABI.
        unsafe {
            let source = Rectangle {
                x: *src_x.get_unchecked(index),
                y: *src_y.get_unchecked(index),
                width: *src_width.get_unchecked(index),
                height: *src_height.get_unchecked(index),
            };
            let dest = Rectangle {
                x: *dest_x.get_unchecked(entity_index) as f32,
                y: *dest_y.get_unchecked(entity_index) as f32,
                width: *dest_width.get_unchecked(entity_index) as f32,
                height: *dest_height.get_unchecked(entity_index) as f32,
            };
            let origin = Vector2 {
                x: *origin_x.get_unchecked(entity_index) as f32,
                y: *origin_y.get_unchecked(entity_index) as f32,
            };
            (fns.draw_texture_pro)(
                texture,
                source,
                dest,
                origin,
                *rotation.get_unchecked(entity_index) as f32,
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

#[cfg(test)]
mod tests {
    use super::*;

    unsafe extern "C" fn draw_texture_pro_a(
        _texture: Texture,
        _source: Rectangle,
        _dest: Rectangle,
        _origin: Vector2,
        _rotation: f32,
        _color: Color,
    ) {
    }

    unsafe extern "C" fn draw_texture_pro_b(
        _texture: Texture,
        _source: Rectangle,
        _dest: Rectangle,
        _origin: Vector2,
        _rotation: f32,
        _color: Color,
    ) {
    }

    fn backend(draw_texture_pro: DrawTextureProFn) -> RenderBackendFns {
        RenderBackendFns {
            draw_texture_pro,
            draw_texture_pro_addr: draw_texture_pro as usize,
        }
    }

    #[test]
    fn backend_configuration_is_idempotent_for_the_same_address() {
        let storage = OnceLock::new();
        let backend = backend(draw_texture_pro_a);

        assert_eq!(configure_backend_once(&storage, backend), Ok(()));
        assert_eq!(configure_backend_once(&storage, backend), Ok(()));
    }

    #[test]
    fn backend_configuration_rejects_a_different_address() {
        let storage = OnceLock::new();

        assert_eq!(
            configure_backend_once(&storage, backend(draw_texture_pro_a)),
            Ok(())
        );
        assert_eq!(
            configure_backend_once(&storage, backend(draw_texture_pro_b)),
            Err(BackendConfigurationError::AddressMismatch)
        );
    }

    #[test]
    fn raylib_value_types_match_the_expected_c_abi() {
        assert_eq!(mem::size_of::<Texture>(), 20);
        assert_eq!(mem::align_of::<Texture>(), 4);
        assert_eq!(mem::size_of::<Rectangle>(), 16);
        assert_eq!(mem::align_of::<Rectangle>(), 4);
        assert_eq!(mem::size_of::<Vector2>(), 8);
        assert_eq!(mem::align_of::<Vector2>(), 4);
        assert_eq!(mem::size_of::<Color>(), 4);
        assert_eq!(mem::align_of::<Color>(), 1);
    }

    #[test]
    fn batch_validation_accepts_reordered_and_repeated_entities() {
        assert_eq!(
            validate_batch_inputs(&[2, 0, 2], [3, 3, 3, 3], [4, 4, 4, 4, 4, 4, 4]),
            Ok(())
        );
    }

    #[test]
    fn batch_validation_rejects_inconsistent_lengths() {
        assert_eq!(
            validate_batch_inputs(&[0, 1], [2, 1, 2, 2], [2, 2, 2, 2, 2, 2, 2]),
            Err(BatchValidationError::SourceArrayLength)
        );
        assert_eq!(
            validate_batch_inputs(&[0, 1], [2, 2, 2, 2], [2, 2, 1, 2, 2, 2, 2]),
            Err(BatchValidationError::DrawViewLength)
        );
    }

    #[test]
    fn batch_validation_rejects_invalid_entity_indices() {
        assert_eq!(
            validate_batch_inputs(&[-1], [1, 1, 1, 1], [1, 1, 1, 1, 1, 1, 1]),
            Err(BatchValidationError::NegativeEntityIndex)
        );
        assert_eq!(
            validate_batch_inputs(&[1], [1, 1, 1, 1], [1, 1, 1, 1, 1, 1, 1]),
            Err(BatchValidationError::EntityIndexOutOfRange)
        );
    }
}

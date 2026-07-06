//! # Trezor App SDK
//!
//! A `no_std` SDK for developing Trezor applications in Rust.
//!
//! ## What this SDK provides
//!
//! - **UI API**: High-level functions for user interaction (confirm dialogs, display, etc.)
//! - **Crypto API**: Cryptographic primitives and operations
//! - **Logging**: Structured logging macros (`trace!`, `info!`, `error!`, etc.) with compile-time filtering
//! - **IPC Services**: [`service`] module for communicating with the core app via IPC messages
//! - **Error handling**: [`Error`] and [`ResultExt::context`] for rich error context
//!   (context strings are only kept in `debug + alloc` builds; stripped in release)
//! - **Essential symbols**: Panic handler, `eh_personality`, and other required `no_std` symbols
//! - **`unwrap!` macro**: Fatal-error variant of `.unwrap()` — see [`macros`]
//!
//! ## Features
//!
//! - `alloc`: Enables heap allocation support (requires initializing an allocator in your app)
//! - `debug`: Enables debug logging and richer error context via [`ResultExt::context`]
//! - `test`: Enables std-based testing utilities
//!
//! ## Quick Start
//!
//! ```rust,ignore
//! use trezor_app_sdk::{trace, error, Error, Result, CORE_SERVICE};
//! use trezor_app_sdk::service::{CoreIpcService, Timeout};
//!
//! #[unsafe(no_mangle)]
//! pub fn app() -> Result<()> {
//!     use core::mem::MaybeUninit;
//!     const HEAP_SIZE: usize = 4096;
//!     static mut HEAP_MEM: [MaybeUninit<u8>; HEAP_SIZE] = [MaybeUninit::uninit(); HEAP_SIZE];
//!     unsafe { HEAP.init(&raw mut HEAP_MEM as usize, HEAP_SIZE) }
//!
//!     loop {
//!         trace!("Waiting for message");
//!         let message = CORE_SERVICE
//!             .receive(Timeout::max())
//!             .map_err(Into::into)
//!             .context("Timeout while receiving message")?;
//!         match message.service().into() {
//!             CoreIpcService::WireStart => {
//!                 handle_wire_message(&message).context("Error handling wire message")?
//!             }
//!             _ => {
//!                 error!("Invalid service invoked");
//!                 return Err(Error::InvalidFunction);
//!             }
//!         };
//!     }
//! }
//! ```

#![cfg_attr(not(feature = "test"), no_std)]
#![allow(internal_features)]
#![allow(dead_code)]
#![feature(core_intrinsics)]
#![cfg_attr(all(feature = "debug", not(feature = "test")), feature(lang_items))]

#[cfg(feature = "alloc")]
mod critical_section;
#[cfg(feature = "alloc")]
mod ipc;
// Internal low-level API module
#[cfg(feature = "alloc")]
mod core_services;
#[cfg(feature = "alloc")]
mod low_level_api;
#[cfg(feature = "alloc")]
mod sysevent;

// Public modules
#[cfg(feature = "alloc")]
pub mod alloc_types;
#[cfg(feature = "alloc")]
pub mod crypto;
#[cfg(feature = "alloc")]
pub mod log;
#[cfg(feature = "alloc")]
pub mod print;
#[cfg(feature = "alloc")]
pub mod service;
pub mod structs;
#[cfg(feature = "alloc")]
pub mod ui;
#[cfg(feature = "alloc")]
pub mod util;

#[cfg(feature = "test")]
pub mod mock;

#[cfg(feature = "alloc")]
#[macro_use]
pub mod macros;

/// A wrapper which aligns its inner value to 4 bytes.
#[cfg(feature = "alloc")]
#[repr(C, align(8))]
pub struct Align<T>(
    /// The inner value.
    pub T,
);

// Re-export UI archived types
#[cfg(feature = "alloc")]
pub use ui::{ArchivedTrezorUiEnum, ArchivedTrezorUiResult};

#[cfg(feature = "alloc")]
#[cfg_attr(any(feature = "debug", feature = "test"), derive(Debug))]
pub enum Error {
    ApiError(ApiError),
    ServiceError,
    DataError(&'static str),
    Cancelled,
    InvalidFunction,
    InvalidMessage,
    InvalidArgument,
    ValueError(&'static str),
    #[cfg(feature = "debug")]
    Context {
        context: &'static str,
        source: Box<Error>,
    },
}

#[cfg(feature = "alloc")]
impl Error {
    pub fn code(&self) -> u16 {
        match self {
            // Keep API error code space separate from local SDK errors.
            Self::ApiError(_) => 1,
            Self::ServiceError => 2,
            Self::DataError(_) => 3,
            Self::Cancelled => 4,
            Self::InvalidFunction => 5,
            Self::InvalidMessage => 6,
            Self::InvalidArgument => 7,
            Self::ValueError(_) => 8,
            #[cfg(feature = "debug")]
            Self::Context { source, .. } => source.code(),
        }
    }

    pub fn message(&self) -> &'static str {
        match self {
            Self::ApiError(_) => "",
            Self::ServiceError => "",
            Self::InvalidFunction => "",
            Self::InvalidMessage => "",
            Self::InvalidArgument => "",
            Self::DataError(msg) => msg,
            Self::ValueError(msg) => msg,
            Self::Cancelled => "",
            #[cfg(feature = "debug")]
            Self::Context { source, .. } => source.message(),
        }
    }

    pub fn error_type(&self) -> &'static str {
        match self {
            Self::ApiError(_) => "ApiError",
            Self::ServiceError => "ServiceError",
            Self::DataError(_) => "DataError",
            Self::Cancelled => "Cancelled",
            Self::InvalidFunction => "InvalidFunction",
            Self::InvalidMessage => "InvalidMessage",
            Self::InvalidArgument => "InvalidArgument",
            Self::ValueError(_) => "ValueError",
            #[cfg(feature = "debug")]
            Self::Context { source, .. } => source.error_type(),
        }
    }

    #[cfg(feature = "debug")]
    pub fn context(self, context: &'static str) -> Self {
        Error::Context {
            context,
            source: Box::new(self),
        }
    }
    #[cfg(not(feature = "debug"))]
    pub fn context(self, _context: &'static str) -> Self {
        self
    }

    #[cfg(feature = "debug")]
    pub fn source(&self) -> Option<&Error> {
        match self {
            Error::Context { source, .. } => Some(&*source),
            _ => None,
        }
    }
}

#[cfg(all(feature = "alloc", feature = "debug"))]
impl ufmt::uDisplay for Error {
    fn fmt<W: ?Sized>(&self, f: &mut ufmt::Formatter<'_, W>) -> core::result::Result<(), W::Error>
    where
        W: ufmt::uWrite,
    {
        // Print the main error line
        match self {
            Error::Context { context, .. } => {
                ufmt::uwrite!(f, "{}", context)?;
            }
            _ => {
                ufmt::uwrite!(f, "{}: {}", self.error_type(), self.message())?;
            }
        }

        // Print the context chain
        let mut source = self.source();
        while let Some(err) = source {
            match err {
                Error::Context { context, .. } => {
                    ufmt::uwrite!(f, "\nCaused by: {}", context)?;
                }
                _ => {
                    ufmt::uwrite!(f, "\nCaused by: {}: {}", err.error_type(), err.message())?;
                }
            }
            source = err.source();
        }
        Ok(())
    }
}

#[cfg(all(feature = "alloc", not(feature = "debug")))]
impl ufmt::uDisplay for Error {
    fn fmt<W: ?Sized>(&self, f: &mut ufmt::Formatter<'_, W>) -> core::result::Result<(), W::Error>
    where
        W: ufmt::uWrite,
    {
        ufmt::uwrite!(f, "{}: {}", self.error_type(), self.message())?;
        Ok(())
    }
}

#[cfg(feature = "alloc")]
impl From<ApiError> for Error {
    fn from(error: ApiError) -> Self {
        Error::ApiError(error)
    }
}

#[cfg(feature = "alloc")]
impl From<service::Error<'_>> for Error {
    fn from(_error: service::Error) -> Self {
        Error::ServiceError
    }
}

#[cfg(feature = "alloc")]
pub trait ResultExt<T> {
    fn context(self, context: &'static str) -> Self;
}

#[cfg(feature = "alloc")]
impl<T> ResultExt<T> for Result<T> {
    fn context(self, context: &'static str) -> Self {
        self.map_err(|e| e.context(context))
    }
}

// The application provides an unmangled Rust function `app` that returns Result<()>
#[cfg(all(feature = "alloc", not(feature = "test")))]
unsafe extern "Rust" {
    unsafe fn app() -> Result<()>;
}

/// Result type alias
#[cfg(feature = "alloc")]
pub use low_level_api::ApiError;

#[cfg(feature = "alloc")]
pub type Result<T> = core::result::Result<T, Error>;

#[cfg(feature = "alloc")]
pub use ipc::IpcMessage;

#[cfg(feature = "alloc")]
static_service!(CORE_SERVICE, CoreApp, service::CoreIpcService, 16384);

#[cfg(all(feature = "alloc", not(feature = "test")))]
#[unsafe(no_mangle)]
pub unsafe extern "C" fn applet_main(
    api_get: low_level_api::ffi::trezor_api_getter_t,
) -> core::ffi::c_int {
    // SAFETY: trusting the caller of applet_main to provide us with a valid getter
    unsafe { low_level_api::init(api_get) };

    CORE_SERVICE.start();
    core_services::init(&CORE_SERVICE);

    // Call the user's app function
    let result = unsafe { app() };

    match result {
        Ok(()) => {
            _ = low_level_api::system_exit();
        }
        Err(e) => {
            error!("Application error");
            let mut error_buf = [0u8; 256];
            let mut writer = util::SliceWriter::new(&mut error_buf);
            _ = ufmt::uwrite!(
                writer,
                "Application failed with error type: {} code: {} and message: {}",
                e.error_type(),
                e.code(),
                e.message()
            );
            error!("{}", e);
            _ = low_level_api::system_exit_error("Error", writer.as_ref(), "");
        }
    }
}

#[cfg(all(feature = "alloc", feature = "debug", not(feature = "test")))]
#[panic_handler]
fn panic_handler(info: &core::panic::PanicInfo<'_>) -> ! {
    let msg = info.message().as_str().unwrap_or("PANIC");
    let (file, line) = info
        .location()
        .map(|loc| {
            // Show only the file name, not the full path
            let file = loc.file();
            let file_short = file.rsplit('/').next().unwrap_or(file);
            (file_short, loc.line() as i32)
        })
        .unwrap_or(("<unknown>", 0));
    low_level_api::system_exit_fatal(msg, file, line);
}

#[cfg(all(feature = "alloc", feature = "debug", not(feature = "test")))]
#[lang = "eh_personality"]
fn eh_personality() -> ! {
    loop {}
}

#[cfg(all(feature = "alloc", feature = "debug", not(feature = "test")))]
#[unsafe(no_mangle)]
unsafe extern "C" fn _Unwind_Resume() {
    unsafe { core::intrinsics::unreachable() };
}

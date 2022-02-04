#![forbid(unsafe_code)]

pub mod base;
pub mod empty;
pub mod label;
pub mod map;
pub mod maybe;
pub mod pad;
pub mod text;
pub mod tuple;

pub use base::{Child, Component, ComponentExt, Event, EventCtx, Never, TimerToken};
pub use empty::Empty;
pub use label::{Label, LabelStyle};
pub use maybe::Maybe;
pub use pad::Pad;
pub use text::{
    formatted::FormattedText,
    layout::{LineBreaking, PageBreaking, TextLayout},
};

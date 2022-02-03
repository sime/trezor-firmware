use core::time::Duration;

use heapless::Vec;

use crate::ui::component::{EventCtx, TimerToken};

/// Contains state commonly used in implementations multi-tap keyboards.
pub struct MultiTapKeyboard {
    /// Configured timeout after which we cancel currently pending key.
    timeout: Duration,
    /// The currently pending state.
    pending: Option<Pending>,
}

struct Pending {
    /// Index of the pending key.
    key: usize,
    /// Index of character inside the pending key.
    char: usize,
    /// Timer for clearing the pending state.
    timer: TimerToken,
}

impl MultiTapKeyboard {
    /// Create a new, empty, multi-tap state.
    pub fn new() -> Self {
        Self {
            timeout: Duration::from_secs(1),
            pending: None,
        }
    }

    /// Return the index of the currently pending key, if any.
    pub fn pending_key(&self) -> Option<usize> {
        self.pending.as_ref().map(|p| p.key)
    }

    /// Return the token for the currently pending timer.
    pub fn pending_timer(&self) -> Option<TimerToken> {
        self.pending.as_ref().map(|p| p.timer)
    }

    /// Reset to the empty state. Takes `EventCtx` to request a paint pass (to
    /// either hide or show any pending marker our caller might want to draw
    /// later).
    pub fn clear_pending_state(&mut self, ctx: &mut EventCtx) {
        if self.pending.is_some() {
            self.pending = None;
            ctx.request_paint();
        }
    }

    /// Register a click to a key. `MultiTapKeyboard` itself does not have any
    /// concept of the key set, so both the key index and the key content is
    /// taken here. Takes `TextBox` as the output buffer, and `EventCtx` to
    /// request paint passes in case of any output modifications, and to request
    /// a timeout for cancelling the pending state. Caller is required to handle
    /// the timer event and call `Self::clear_pending_state` when the timer
    /// hits.
    pub fn click_key<const L: usize>(
        &mut self,
        ctx: &mut EventCtx,
        key: usize,
        key_text: &[u8],
        textbox: &mut TextBox<L>,
    ) {
        enum Op {
            Replace,
            Append,
        }
        let (op, char) = match &self.pending {
            Some(pending) if pending.key == key => {
                // This key is pending. Cycle the last inserted character through the
                // key content.
                (Op::Replace, (pending.char + 1) % key_text.len())
            }
            _ => {
                // This key is not pending. Append the first character in the key.
                (Op::Append, 0)
            }
        };
        match op {
            Op::Replace => textbox.replace_last(ctx, key_text[char]),
            Op::Append => textbox.append(ctx, key_text[char]),
        }

        // If the key has more then one character, we need to set it as pending, so we
        // can cycle through on the repeated clicks. We also request a timer so we can
        // reset the pending state after a deadline.
        //
        // Note: It might seem that we should make sure to `request_paint` in case we
        // progress into a pending state (to display the pending marker), but such
        // transition only happens as a result of an append op, so the `TextBox` should
        // have already requested painting.
        self.pending = if key_text.len() > 1 {
            Some(Pending {
                key,
                char,
                timer: ctx.request_timer(self.timeout),
            })
        } else {
            None
        };
    }
}

/// Wraps a character buffer of maximum length `L` and provides text editing
/// operations over it. Text ops usually take a `EventCtx` to request a paint
/// pass in case of any state modification.
pub struct TextBox<const L: usize> {
    text: Vec<u8, L>,
}

impl<const L: usize> TextBox<L> {
    /// Create a new `TextBox` with content `text`.
    pub fn new(text: Vec<u8, L>) -> Self {
        Self { text }
    }

    /// Create an empty `TextBox`.
    pub fn empty() -> Self {
        Self::new(Vec::new())
    }

    pub fn content(&self) -> &[u8] {
        &self.text
    }

    pub fn is_empty(&self) -> bool {
        self.text.is_empty()
    }

    /// Delete the last character of content, if any.
    pub fn delete_last(&mut self, ctx: &mut EventCtx) {
        let changed = self.text.pop().is_some();
        if changed {
            ctx.request_paint();
        }
    }

    /// Replaces the last character of the content with `char`. If the content
    /// is empty, `char` is appended.
    pub fn replace_last(&mut self, ctx: &mut EventCtx, char: u8) {
        let previous = self.text.pop();
        if self.text.push(char).is_err() {
            #[cfg(feature = "ui_debug")]
            panic!("TextContent has zero capacity");
        }
        let changed = previous != Some(char);
        if changed {
            ctx.request_paint();
        }
    }

    /// Append `char` at the end of the content.
    pub fn append(&mut self, ctx: &mut EventCtx, char: u8) {
        if self.text.push(char).is_err() {
            #[cfg(feature = "ui_debug")]
            panic!("TextContent is full");
        }
        ctx.request_paint();
    }

    /// Replace the textbox content with `text`.
    pub fn replace(&mut self, ctx: &mut EventCtx, text: &[u8]) {
        if self.text != text {
            self.text.clear();
            if self.text.extend_from_slice(text).is_err() {
                #[cfg(feature = "ui_debug")]
                panic!("TextContent is full");
            }
            ctx.request_paint();
        }
    }

    /// Clear the textbox content.
    pub fn clear(&mut self, ctx: &mut EventCtx) {
        self.replace(ctx, b"");
    }
}

/// Analogue to `[T]::enumerate().map(...)`.
pub fn array_map_enumerate<T, U, const L: usize>(
    array: [T; L],
    mut func: impl FnMut(usize, T) -> U,
) -> [U; L] {
    let mut i = 0;
    array.map(|t| {
        let u = func(i, t);
        i += 1;
        u
    })
}

use core::iter;

use heapless::String;

use crate::util::ResultExt;
use crate::{
    trezorhal::slip39,
    ui::{
        component::{Component, Event, EventCtx},
        display,
        geometry::{Offset, Rect},
        model_tt::{
            component::{
                keyboard::{
                    common::{MultiTapKeyboard, TextBox, TextEdit},
                    mnemonic::{MnemonicInput, MnemonicInputMsg, MNEMONIC_KEY_COUNT},
                },
                Button, ButtonContent, ButtonMsg,
            },
            theme,
        },
    },
};

const MAX_LENGTH: usize = 8;

pub struct Slip39Input {
    button: Button,
    textbox: TextBox<MAX_LENGTH>,
    multi_tap: MultiTapKeyboard,
    final_word: Option<&'static str>,
    input_mask: Slip39Mask,
}

impl MnemonicInput for Slip39Input {
    fn new(area: Rect) -> Self {
        Self {
            button: Button::empty(area),
            textbox: TextBox::empty(),
            multi_tap: MultiTapKeyboard::new(),
            final_word: None,
            input_mask: Slip39Mask::full(),
        }
    }

    /// Return the key set. Keys are further specified as indices into this
    /// array.
    fn keys() -> [&'static str; MNEMONIC_KEY_COUNT] {
        ["ab", "cd", "ef", "ghij", "klm", "nopq", "rs", "tuv", "xyz"]
    }

    /// Returns `true` if given key index can continue towards a valid mnemonic
    /// word, `false` otherwise.
    fn can_key_press_lead_to_a_valid_word(&self, key: usize) -> bool {
        if self.input_mask.is_final() {
            false
        } else {
            // Currently pending key is always enabled.
            // Keys that mach the completion mask are enabled as well.
            self.multi_tap.pending_key() == Some(key) || self.input_mask.contains_key(key)
        }
    }

    /// Key button was clicked. If this button is pending, let's cycle the
    /// pending character in textbox. If not, let's just append the first
    /// character.
    fn on_key_click(&mut self, ctx: &mut EventCtx, key: usize) {
        let edit = self.multi_tap.click_key(ctx, key, Self::keys()[key]);
        if let TextEdit::Append(_) = edit {
            // This key press wasn't just a pending key rotation, so let's push the key
            // digit to the buffer.
            self.textbox.append(ctx, Self::key_digit(key));
        } else {
            // Ignore the pending char rotation. We use the pending key to paint
            // the last character, but the mnemonic word computation depends
            // only on the pressed key, not on the specific character inside it.
        }
        self.complete_word_from_dictionary(ctx);
    }

    /// Backspace button was clicked, let's delete the last character of input
    /// and clear the pending marker.
    fn on_backspace_click(&mut self, ctx: &mut EventCtx) {
        self.multi_tap.clear_pending_state(ctx);
        self.textbox.delete_last(ctx);
        self.complete_word_from_dictionary(ctx);
    }

    fn is_empty(&self) -> bool {
        self.textbox.is_empty()
    }
}

impl Component for Slip39Input {
    type Msg = MnemonicInputMsg;

    fn event(&mut self, ctx: &mut EventCtx, event: Event) -> Option<Self::Msg> {
        if matches!((event, self.multi_tap.pending_timer()), (Event::Timer(t), Some(pt)) if pt == t)
        {
            // Timeout occurred. Reset the pending key.
            self.multi_tap.clear_pending_state(ctx);
            return Some(MnemonicInputMsg::TimedOut);
        }
        if let Some(ButtonMsg::Clicked) = self.button.event(ctx, event) {
            // Input button was clicked.  If the whole word is totally identified, let's
            // confirm it, otherwise don't do anything.
            if self.input_mask.is_final() {
                return Some(MnemonicInputMsg::Confirmed);
            }
        }
        None
    }

    fn paint(&mut self) {
        let area = self.button.area();
        let style = self.button.style();

        // First, paint the button background.
        self.button.paint_background(&style);

        // Content starts in the left-center point, offset by 16px to the right and 8px
        // to the bottom.
        let text_baseline = area.top_left().center(area.bottom_left()) + Offset::new(16, 8);

        // To simplify things, we always copy the printed string here, even if it
        // wouldn't be strictly necessary.
        let mut text: String<MAX_LENGTH> = String::new();

        if let Some(word) = self.final_word {
            // We're done with input, paint the full word.
            text.push_str(word)
                .assert_if_debugging_ui("Text buffer is too small");
        } else {
            // Paint an asterisk for each letter of input.
            for ch in iter::repeat('*').take(self.textbox.content().len()) {
                text.push(ch)
                    .assert_if_debugging_ui("Text buffer is too small");
            }
            // If we're in the pending state, paint the pending character at the end.
            if let (Some(key), Some(press)) =
                (self.multi_tap.pending_key(), self.multi_tap.pending_press())
            {
                let ascii_text = Self::keys()[key].as_bytes();
                let ch = ascii_text[press % ascii_text.len()] as char;
                text.pop();
                text.push(ch)
                    .assert_if_debugging_ui("Text buffer is too small");
            }
        }
        display::text(
            text_baseline,
            text.as_bytes(),
            style.font,
            style.text_color,
            style.button_color,
        );
        let width = style.font.text_width(text.as_bytes());

        // Paint the pending marker.
        if self.multi_tap.pending_key().is_some() && self.final_word.is_none() {
            // Measure the width of the last character of input.
            if let Some(last) = text.as_bytes().last().copied() {
                let last_width = style.font.text_width(&[last]);
                // Draw the marker 2px under the start of the baseline of the last character.
                let marker_origin = text_baseline + Offset::new(width - last_width, 2);
                // Draw the marker 1px longer than the last character, and 3px thick.
                let marker_rect =
                    Rect::from_top_left_and_size(marker_origin, Offset::new(last_width + 1, 3));
                display::rect(marker_rect, style.text_color);
            }
        }

        // Paint the icon.
        if let ButtonContent::Icon(icon) = self.button.content() {
            // Icon is painted in the right-center point, of expected size 16x16 pixels, and
            // 16px from the right edge.
            let icon_center = area.top_right().center(area.bottom_right()) - Offset::new(16 + 8, 0);
            display::icon(icon_center, icon, style.text_color, style.button_color);
        }
    }
}

impl Slip39Input {
    /// Convert a key index into the key digit. This is what we push into the
    /// input buffer.
    ///
    /// # Examples
    ///
    /// ```
    /// Self::key_digit(0) == '1';
    /// Self::key_digit(1) == '2';
    /// ```
    fn key_digit(key: usize) -> char {
        let index = key + 1;
        char::from_digit(index as u32, 10).unwrap()
    }

    fn complete_word_from_dictionary(&mut self, ctx: &mut EventCtx) {
        let sequence = self.input_sequence();
        self.final_word = sequence.and_then(slip39::button_sequence_to_word);
        self.input_mask = sequence
            .and_then(slip39::word_completion_mask)
            .map(Slip39Mask)
            .unwrap_or_else(Slip39Mask::full);

        // Change the style of the button depending on the input.
        if self.final_word.is_some() {
            // Confirm button.
            self.button.enable(ctx);
            self.button.set_stylesheet(ctx, theme::button_confirm());
            self.button
                .set_content(ctx, ButtonContent::Icon(theme::ICON_CONFIRM));
        } else {
            // Disabled button.
            self.button.disable(ctx);
            self.button.set_stylesheet(ctx, theme::button_default());
            self.button.set_content(ctx, ButtonContent::Text(b""));
        }
    }

    fn input_sequence(&self) -> Option<u16> {
        self.textbox.content().parse().ok()
    }
}

struct Slip39Mask(u16);

impl Slip39Mask {
    /// Return a mask with all keys allowed.
    fn full() -> Self {
        Self(0x1FF) // All buttons are allowed. 9-bit bitmap all set to 1.
    }

    /// Returns `true` if `key` can lead to a valid SLIP39 word with this mask.
    fn contains_key(&self, key: usize) -> bool {
        self.0 & (1 << key) != 0
    }

    /// Returns `true` if mask has exactly one bit set to 1, or is equal to 0.
    fn is_final(&self) -> bool {
        self.0.count_ones() <= 1
    }
}

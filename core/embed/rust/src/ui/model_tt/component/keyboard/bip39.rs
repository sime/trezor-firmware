use crate::{
    trezorhal::bip39,
    ui::{
        component::{Child, Component, Event, EventCtx},
        display,
        geometry::{Grid, Offset, Rect},
        model_tt::{
            component::{
                keyboard::common::{array_map_enumerate, MultiTapKeyboard, TextBox},
                Button, ButtonContent, ButtonMsg,
            },
            theme,
        },
    },
};

pub enum Bip39KeyboardMsg {
    Confirmed,
    Cancelled,
}

const KEYS: [&[u8]; 9] = [
    b"abc", b"def", b"ghi", b"jkl", b"mno", b"pqr", b"stu", b"vwx", b"yz",
];

const MAX_WORD_LEN: usize = 8;

struct Bip39Input {
    button: Button,
    textbox: TextBox<MAX_WORD_LEN>,
    multi_tap: MultiTapKeyboard,
    completed_word: Option<&'static [u8]>,
}

impl Bip39Input {
    fn new(area: Rect) -> Self {
        Self {
            button: Button::empty(area, theme::button_default()),
            textbox: TextBox::empty(),
            multi_tap: MultiTapKeyboard::new(),
            completed_word: None,
        }
    }

    fn complete_word_from_dictionary(&mut self) {
        self.completed_word = bip39::complete_word(self.textbox.content());
    }

    fn completion_mask(&self) -> u32 {
        bip39::word_completion_mask(self.textbox.content())
    }
}

impl Component for Bip39Input {
    type Msg = ButtonMsg;

    fn event(&mut self, ctx: &mut EventCtx, event: Event) -> Option<Self::Msg> {
        self.button.event(ctx, event)
    }

    fn paint(&mut self) {
        let area = self.button.area();
        let style = self.button.style();

        // First, paint the button background.
        self.button.paint_background(&style);

        // Paint the entered content (the prefix of the suggested word).
        let text = self.textbox.content();
        let width = style.font.text_width(text);
        // Content starts in the left-center point, offset by 16px to the right and 8px
        // to the bottom.
        let text_baseline = area.top_left().center(area.bottom_left()) + Offset::new(16, 8);
        display::text(
            text_baseline,
            text,
            style.font,
            style.text_color,
            style.button_color,
        );

        // Paint the rest of the suggested dictionary word.
        if let Some(word) = self.completed_word.and_then(|w| w.get(text.len()..)) {
            let word_baseline = text_baseline + Offset::new(width, 0);
            display::text(
                word_baseline,
                word,
                style.font,
                theme::GREY,
                style.button_color,
            );
        }

        // Paint the pending marker.
        if self.multi_tap.pending_key().is_some() {
            // Measure the width of the last character of input.
            if let Some(last) = text.last().copied() {
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

pub struct Bip39Keyboard {
    input: Child<Bip39Input>,
    back: Child<Button>,
    keys: [Child<Button>; KEYS.len()],
}

impl Bip39Keyboard {
    pub fn new(area: Rect) -> Self {
        let grid = Grid::new(area, 3, 4);
        let back_area = grid.row_col(0, 0);
        let input_area = grid.row_col(0, 1).union(grid.row_col(0, 2));
        Self {
            input: Child::new(Bip39Input::new(input_area)),
            back: Child::new(Button::with_icon(
                back_area,
                theme::ICON_BACK,
                theme::button_clear(),
            )),
            keys: Self::key_buttons(&grid, grid.cols), // Start in the second row.
        }
    }

    fn key_buttons(grid: &Grid, offset: usize) -> [Child<Button>; KEYS.len()] {
        array_map_enumerate(KEYS, |index, text| {
            Child::new(Button::with_text(
                grid.cell(offset + index),
                text,
                theme::button_default(),
            ))
        })
    }

    /// Key button was clicked. If this button is pending, let's cycle the
    /// pending character in textbox. If not, let's just append the first
    /// character.
    fn on_key_click(&mut self, ctx: &mut EventCtx, clicked_key: usize) {
        // Mutate the text input and get the completion mask and the currently pending
        // key.
        let (mask, pending_key) = self.input.mutate(ctx, |ctx, input| {
            input
                .multi_tap
                .click_key(ctx, clicked_key, KEYS[clicked_key], &mut input.textbox);
            input.complete_word_from_dictionary();
            (input.completion_mask(), input.multi_tap.pending_key())
        });

        // Either enable or disable the key buttons.
        for (key, btn) in self.keys.iter_mut().enumerate() {
            // Currently pending key is always enabled.
            let key_is_pending = pending_key == Some(key);
            // Keys that contain letters from the completion mask are enabled as well.
            let key_matches_mask = Self::compute_mask(KEYS[key]) & mask != 0;
            btn.mutate(ctx, |ctx, b| {
                b.enable_if(ctx, key_is_pending || key_matches_mask)
            });
        }
    }

    /// Backspace button was clicked, let's delete the last character of input
    /// and clear the pending marker.
    fn on_backspace_click(&mut self, ctx: &mut EventCtx) {
        self.input.mutate(ctx, |ctx, input| {
            input.textbox.delete_last(ctx);
            input.multi_tap.clear_pending_state(ctx);
        });
    }

    /// Input button was clicked.  If the content matches the suggested word,
    /// let's confirm it, otherwise just auto-complete.
    fn on_input_click(&mut self, ctx: &mut EventCtx) -> Option<Bip39KeyboardMsg> {
        self.input
            .mutate(ctx, |ctx, input| match input.completed_word {
                Some(word) if word == input.textbox.content() => {
                    input.textbox.clear(ctx);
                    Some(Bip39KeyboardMsg::Confirmed)
                }
                Some(word) => {
                    input.textbox.replace(ctx, word);
                    None
                }
                None => None,
            })
    }

    /// Timeout occurred.  If we can auto-complete current input, let's just
    /// reset the pending marker.  If not, input is invalid, let's backspace the
    /// last character.
    fn on_timeout(&mut self, ctx: &mut EventCtx) {
        self.input.mutate(ctx, |ctx, input| {
            if input.completed_word.is_none() {
                input.textbox.delete_last(ctx);
            }
            input.multi_tap.clear_pending_state(ctx);
        });
    }

    fn compute_mask(key_text: &[u8]) -> u32 {
        let mut mask = 0;
        for ch in key_text {
            // We assume the key text is lower-case alphabetic ASCII, making the subtraction
            // and the shift panic-free.
            mask |= 1 << (ch - b'a');
        }
        mask
    }
}

impl Component for Bip39Keyboard {
    type Msg = Bip39KeyboardMsg;

    fn event(&mut self, ctx: &mut EventCtx, event: Event) -> Option<Self::Msg> {
        let pending_timer = self.input.inner().multi_tap.pending_timer();
        if matches!((event, pending_timer), (Event::Timer(t), Some(pt)) if pt == t) {
            self.on_timeout(ctx);
            return None;
        }
        if let Some(ButtonMsg::Clicked) = self.input.event(ctx, event) {
            if let Some(msg) = self.on_input_click(ctx) {
                return Some(msg);
            }
        }
        if let Some(ButtonMsg::Clicked) = self.back.event(ctx, event) {
            self.on_backspace_click(ctx);
            return None;
        }
        for (key, btn) in self.keys.iter_mut().enumerate() {
            if let Some(ButtonMsg::Clicked) = btn.event(ctx, event) {
                self.on_key_click(ctx, key);
                return None;
            }
        }
        None
    }

    fn paint(&mut self) {
        self.input.paint();
        self.back.paint();
        for btn in &mut self.keys {
            btn.paint();
        }
    }
}

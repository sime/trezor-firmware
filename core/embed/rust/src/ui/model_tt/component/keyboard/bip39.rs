use crate::{
    trezorhal::bip39,
    ui::{
        component::{Child, Component, Event, EventCtx, Label, Maybe},
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

pub struct Bip39Keyboard {
    /// Initial prompt, displayed on empty input.
    prompt: Child<Maybe<Label<&'static [u8]>>>,
    /// Backspace button.
    back: Child<Maybe<Button>>,
    /// Input area, acting as the auto-complete and confirm button.
    input: Child<Maybe<Bip39Input>>,
    /// Key buttons.
    keys: [Child<Button>; KEYS.len()],
}

impl Bip39Keyboard {
    pub fn new(area: Rect, prompt: &'static [u8]) -> Self {
        let grid = Grid::new(area, 3, 4);
        let back_area = grid.row_col(0, 0);
        let input_area = grid.row_col(0, 1).union(grid.row_col(0, 3));
        let prompt_area = grid.row_col(0, 0).union(grid.row_col(0, 3));
        let prompt_origin = prompt_area.top_left();

        Self {
            prompt: Child::new(Maybe::visible(
                prompt_area,
                theme::BG,
                Label::left_aligned(prompt_origin, prompt, theme::label_default()),
            )),
            back: Child::new(Maybe::hidden(
                back_area,
                theme::BG,
                Button::with_icon(back_area, theme::ICON_BACK).styled(theme::button_clear()),
            )),
            input: Child::new(Maybe::hidden(
                input_area,
                theme::BG,
                Bip39Input::new(input_area),
            )),
            keys: Self::key_buttons(&grid, grid.cols), // Start in the second row.
        }
    }

    fn key_buttons(grid: &Grid, offset: usize) -> [Child<Button>; KEYS.len()] {
        array_map_enumerate(KEYS, |index, text| {
            Child::new(Button::with_text(grid.cell(offset + index), text))
        })
    }

    /// Either enable or disable the key buttons, depending on the dictionary
    /// completion mask and the pending key.
    fn toggle_key_buttons(&mut self, ctx: &mut EventCtx) {
        let pending_key = self.input.inner().inner().multi_tap.pending_key();
        let mask = self.input.inner().inner().completion_mask();

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

    /// After edit operations, we need to either show or hide the prompt, the
    /// input, and the back button.
    fn toggle_prompt_or_input(&mut self, ctx: &mut EventCtx) {
        let prompt_visible = self.input.inner().inner().textbox.is_empty();
        self.prompt
            .mutate(ctx, |ctx, p| p.show_if(ctx, prompt_visible));
        self.input
            .mutate(ctx, |ctx, i| i.show_if(ctx, !prompt_visible));
        self.back
            .mutate(ctx, |ctx, b| b.show_if(ctx, !prompt_visible));
    }

    /// Compute a bitmask of all letters contained in given key text. Lowest bit
    /// is 'a', second lowest 'b', etc.
    fn compute_mask(key_text: &[u8]) -> u32 {
        let mut mask = 0;
        for ch in key_text {
            // We assume the key text is lower-case alphabetic ASCII, making the subtraction
            // and the shift panic-free.
            mask |= 1 << (ch - b'a');
        }
        mask
    }

    /// Key button was clicked. If this button is pending, let's cycle the
    /// pending character in textbox. If not, let's just append the first
    /// character.
    fn on_key_click(&mut self, ctx: &mut EventCtx, clicked_key: usize) {
        self.input.mutate(ctx, |ctx, input| {
            let input = input.inner_mut();
            input
                .multi_tap
                .click_key(ctx, clicked_key, KEYS[clicked_key], &mut input.textbox);
            input.complete_word_from_dictionary();
        });
        self.toggle_key_buttons(ctx);
        self.toggle_prompt_or_input(ctx);
    }

    /// Backspace button was clicked, let's delete the last character of input
    /// and clear the pending marker.
    fn on_backspace_click(&mut self, ctx: &mut EventCtx) {
        self.input.mutate(ctx, |ctx, input| {
            let input = input.inner_mut();
            input.textbox.delete_last(ctx);
            input.multi_tap.clear_pending_state(ctx);
        });
        self.toggle_key_buttons(ctx);
        self.toggle_prompt_or_input(ctx);
    }

    /// Input button was clicked.  If the content matches the suggested word,
    /// let's confirm it, otherwise just auto-complete.
    fn on_input_click(&mut self, ctx: &mut EventCtx) -> Option<Bip39KeyboardMsg> {
        let msg = self.input.mutate(ctx, |ctx, input| {
            let input = input.inner_mut();
            match input.completed_word {
                Some(word) if word == input.textbox.content() => {
                    input.textbox.clear(ctx);
                    Some(Bip39KeyboardMsg::Confirmed)
                }
                Some(word) => {
                    input.textbox.replace(ctx, word);
                    None
                }
                None => None,
            }
        });
        self.toggle_key_buttons(ctx);
        self.toggle_prompt_or_input(ctx);
        msg
    }

    /// Timeout occurred.  If we can auto-complete current input, let's just
    /// reset the pending marker.  If not, input is invalid, let's backspace the
    /// last character.
    fn on_timeout(&mut self, ctx: &mut EventCtx) {
        self.input.mutate(ctx, |ctx, input| {
            let input = input.inner_mut();
            if input.completed_word.is_none() {
                input.textbox.delete_last(ctx);
            }
            input.multi_tap.clear_pending_state(ctx);
        });
        self.toggle_key_buttons(ctx);
        self.toggle_prompt_or_input(ctx);
    }
}

impl Component for Bip39Keyboard {
    type Msg = Bip39KeyboardMsg;

    fn event(&mut self, ctx: &mut EventCtx, event: Event) -> Option<Self::Msg> {
        match self.input.event(ctx, event) {
            Some(Bip39InputMsg::Button(ButtonMsg::Clicked)) => {
                if let Some(msg) = self.on_input_click(ctx) {
                    return Some(msg);
                }
            }
            Some(Bip39InputMsg::TimedOut) => {
                self.on_timeout(ctx);
            }
            _ => {}
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
        self.prompt.paint();
        self.input.paint();
        self.back.paint();
        for btn in &mut self.keys {
            btn.paint();
        }
    }
}

enum Bip39InputMsg {
    Button(ButtonMsg),
    TimedOut,
}

struct Bip39Input {
    button: Button,
    textbox: TextBox<MAX_WORD_LEN>,
    multi_tap: MultiTapKeyboard,
    completed_word: Option<&'static [u8]>,
}

impl Bip39Input {
    fn new(area: Rect) -> Self {
        Self {
            button: Button::empty(area),
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
    type Msg = Bip39InputMsg;

    fn event(&mut self, ctx: &mut EventCtx, event: Event) -> Option<Self::Msg> {
        match (event, self.multi_tap.pending_timer()) {
            (Event::Timer(t), Some(pt)) if pt == t => Some(Bip39InputMsg::TimedOut),
            _ => self.button.event(ctx, event).map(Bip39InputMsg::Button),
        }
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

use cstr_core::CStr;

mod ffi {
    extern "C" {
        // trezor-crypto/slip39.h
        pub fn slip39_word_completion_mask(prefix: u16) -> u16;
        pub fn button_sequence_to_word(sequence: u16) -> *const cty::c_char;
    }
}

/// Calculates which buttons still can be pressed after some already were.
/// Returns a 9-bit bitmask, where each bit specifies which buttons
/// can be further pressed (there are still words in this combination).
/// LSB denotes first button.
///
/// Example: 110000110 - second, third, eighth and ninth button still can be
/// pressed.
pub fn word_completion_mask(prefix: u16) -> Option<u16> {
    if prefix < 1 || prefix > 9999 {
        None
    } else {
        Some(unsafe { ffi::slip39_word_completion_mask(prefix) })
    }
}

/// Finds the first word that fits the given button prefix.
pub fn button_sequence_to_word(prefix: u16) -> Option<&'static str> {
    let word = unsafe { ffi::button_sequence_to_word(prefix) };
    if word.is_null() {
        None
    } else {
        // SAFETY: On success, `button_sequence_to_word` should return a 0-terminated
        // UTF-8 string with static lifetime.
        Some(unsafe { CStr::from_ptr(word).to_str().unwrap_unchecked() })
    }
}

use cstr_core::CStr;

extern "C" {
    // trezor-crypto/bip39.h
    fn mnemonic_complete_word(prefix: *const cty::c_char, len: cty::c_int) -> *const cty::c_char;
    fn mnemonic_word_completion_mask(prefix: *const cty::c_char, len: cty::c_int) -> u32;
}

pub fn complete_word(prefix: &[u8]) -> Option<&'static [u8]> {
    if prefix.is_empty() {
        None
    } else {
        // SAFETY: `mnemonic_complete_word` shouldn't retain nor modify the passed byte
        // string, making the call safe.
        let word = unsafe { mnemonic_complete_word(prefix.as_ptr() as _, prefix.len() as _) };
        if word.is_null() {
            None
        } else {
            // SAFETY: On success, `mnemonic_complete_word` should return a 0-terminated
            // string with static lifetime.
            Some(unsafe { CStr::from_ptr(word).to_bytes() })
        }
    }
}

pub fn word_completion_mask(prefix: &[u8]) -> u32 {
    // SAFETY: `mnemonic_word_completion_mask` shouldn't retain nor modify the
    // passed byte string, making the call safe.
    unsafe { mnemonic_word_completion_mask(prefix.as_ptr() as _, prefix.len() as _) }
}

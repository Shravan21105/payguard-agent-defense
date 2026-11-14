use near_sdk::{env, PublicKey};
use crate::types::PolicyAuthorization;

pub fn parse_hex_signature(sig_hex: &str) -> Option<[u8; 64]> {
    let clean_hex = sig_hex.strip_prefix("0x").unwrap_or(sig_hex);
    if clean_hex.len() != 128 {
        return None;
    }
    let bytes = hex::decode(clean_hex).ok()?;
    if bytes.len() != 64 {
        return None;
    }
    let mut arr = [0u8; 64];
    arr.copy_from_slice(&bytes);
    Some(arr)
}

pub fn extract_ed25519_pubkey_bytes(pk: &PublicKey) -> Option<[u8; 32]> {
    let pk_bytes = pk.as_bytes();
    // NEAR PublicKey wire format for Ed25519: byte 0 is 0 (CurveType::ED25519), followed by 32 bytes key.
    if pk_bytes.len() == 33 && pk_bytes[0] == 0 {
        let mut arr = [0u8; 32];
        arr.copy_from_slice(&pk_bytes[1..33]);
        Some(arr)
    } else if pk_bytes.len() == 32 {
        let mut arr = [0u8; 32];
        arr.copy_from_slice(pk_bytes);
        Some(arr)
    } else {
        None
    }
}

pub fn verify_policy_signature(
    auth: &PolicyAuthorization,
    signature_hex: &str,
    signer_pk: &PublicKey,
) -> bool {
    let sig_bytes = match parse_hex_signature(signature_hex) {
        Some(s) => s,
        None => return false,
    };

    let pk_bytes = match extract_ed25519_pubkey_bytes(signer_pk) {
        Some(k) => k,
        None => return false,
    };

    let canonical_msg = auth.to_canonical_bytes();

    #[cfg(not(target_arch = "wasm32"))]
    {
        // For unit testing off-chain on native targets where NEAR VM host functions might not be linked,
        // use standard ed25519 or VM mock verification if available
        env::ed25519_verify(&sig_bytes, &canonical_msg, &pk_bytes)
    }

    #[cfg(target_arch = "wasm32")]
    {
        env::ed25519_verify(&sig_bytes, &canonical_msg, &pk_bytes)
    }
}


use near_sdk::json_types::U128;
use near_sdk::{env, AccountId};
use serde::Serialize;

#[derive(Serialize)]
#[serde(crate = "near_sdk::serde")]
#[serde(tag = "event", content = "data")]
#[serde(rename_all = "snake_case")]
pub enum PayguardEventData {
    TransferExecuted {
        auth_id: String,
        sender_id: AccountId,
        recipient_id: AccountId,
        amount: U128,
        risk_score: u8,
    },
    EscrowCreated {
        escrow_id: String,
        auth_id: String,
        sender_id: AccountId,
        recipient_id: AccountId,
        amount: U128,
        risk_score: u8,
        timelock_until: u64,
    },
    EscrowApproved {
        escrow_id: String,
        approved_by: AccountId,
    },
    EscrowReleased {
        escrow_id: String,
        recipient_id: AccountId,
        amount: U128,
    },
    EscrowRejected {
        escrow_id: String,
        rejected_by: AccountId,
        sender_id: AccountId,
        amount: U128,
        reason: String,
    },
    TransferBlocked {
        auth_id: String,
        sender_id: AccountId,
        recipient_id: AccountId,
        risk_score: u8,
        reason: String,
    },
    VaultPaused {
        is_paused: bool,
    },
    SignerUpdated {
        new_signer_pk: String,
    },
}

#[derive(Serialize)]
#[serde(crate = "near_sdk::serde")]
struct Nep297Event<'a> {
    standard: &'static str,
    version: &'static str,
    #[serde(flatten)]
    event_data: &'a PayguardEventData,
}

pub fn emit_event(event: PayguardEventData) {
    let nep = Nep297Event {
        standard: "payguard_vault",
        version: "1.0.0",
        event_data: &event,
    };
    if let Ok(json) = serde_json::to_string(&nep) {
        env::log_str(&format!("EVENT_JSON:{}", json));
    }
}


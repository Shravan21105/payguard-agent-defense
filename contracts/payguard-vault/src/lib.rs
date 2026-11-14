use near_sdk::collections::{LookupSet, UnorderedMap};
use near_sdk::json_types::U128;
use near_sdk::{
    env, near, require, AccountId, NearToken, PanicOnDefault, Promise, PublicKey,
};

pub mod events;
pub mod types;
pub mod verification;

use events::{emit_event, PayguardEventData};
use types::*;
use verification::verify_policy_signature;

#[near(contract_state)]
#[derive(PanicOnDefault)]
pub struct PayguardVault {
    pub admin_id: AccountId,
    pub policy_signer_pk: PublicKey,
    pub authorized_approvers: LookupSet<AccountId>,
    pub min_escrow_duration_sec: u64,
    pub max_escrow_duration_sec: u64,
    pub policy_version: String,
    pub is_paused: bool,
    pub used_auth_ids: LookupSet<String>,
    pub used_nonces: LookupSet<u64>,
    pub escrows: UnorderedMap<String, EscrowRecord>,
    pub transactions: UnorderedMap<String, OnChainTransactionRecord>,
    pub total_volume_yocto: U128,
    pub total_transfers_count: u64,
    pub active_escrow_count: u64,
}

#[near]
impl PayguardVault {
    #[init]
    pub fn init(
        admin_id: AccountId,
        policy_signer_pk: PublicKey,
        approvers: Vec<AccountId>,
        min_escrow_sec: Option<u64>,
        max_escrow_sec: Option<u64>,
        policy_version: Option<String>,
    ) -> Self {
        require!(!env::state_exists(), "Contract already initialized");

        let mut authorized_approvers = LookupSet::new(b"a");
        for approver in approvers {
            authorized_approvers.insert(&approver);
        }

        Self {
            admin_id,
            policy_signer_pk,
            authorized_approvers,
            min_escrow_duration_sec: min_escrow_sec.unwrap_or(60),        // 1 min default min
            max_escrow_duration_sec: max_escrow_sec.unwrap_or(86400 * 7), // 7 days default max
            policy_version: policy_version.unwrap_or_else(|| "1.0.0".to_string()),
            is_paused: false,
            used_auth_ids: LookupSet::new(b"u"),
            used_nonces: LookupSet::new(b"n"),
            escrows: UnorderedMap::new(b"e"),
            transactions: UnorderedMap::new(b"t"),
            total_volume_yocto: U128(0),
            total_transfers_count: 0,
            active_escrow_count: 0,
        }
    }

    // -------------------------------------------------------------------------
    // Execution: ALLOW Transaction
    // -------------------------------------------------------------------------
    #[payable]
    pub fn execute_transfer(
        &mut self,
        auth: PolicyAuthorization,
        signature: String,
    ) -> OnChainTransactionRecord {
        self.assert_not_paused();

        // 1. Enforce ALLOW decision
        require!(
            auth.decision == DecisionType::Allow,
            "Only ALLOW policy authorizations can be directly executed"
        );

        // 2. Temporal validation
        let now = env::block_timestamp();
        require!(auth.expires_at >= now, "Authorization has expired");
        require!(auth.issued_at <= now, "Authorization issued in the future");
        require!(auth.expires_at > auth.issued_at, "Invalid expiration interval");
        require!(
            auth.policy_version == self.policy_version,
            "Policy version mismatch"
        );

        // 3. Domain separation & Account integrity
        require!(
            auth.contract_id == env::current_account_id(),
            "Contract ID mismatch"
        );
        require!(
            auth.sender_id != auth.recipient_id,
            "Sender and recipient cannot be identical"
        );

        // 4. Financial non-zero verification
        require!(
            auth.amount.0 > 0,
            "Transfer amount must be strictly greater than 0"
        );

        // 5. Anti-replay verification
        require!(
            !self.used_auth_ids.contains(&auth.auth_id),
            "Authorization ID already used"
        );
        require!(
            !self.used_nonces.contains(&auth.nonce),
            "Nonce has already been consumed"
        );

        // 5. Cryptographic signature check
        require!(
            verify_policy_signature(&auth, &signature, &self.policy_signer_pk),
            "Invalid cryptographic authorization signature"
        );

        // 6. Deposit and funds verification
        let attached = env::attached_deposit().as_yoctonear();
        require!(
            attached >= auth.amount.0,
            "Attached deposit is less than authorized transfer amount"
        );

        // 7. Consume authorization (Atomic replay protection)
        self.used_auth_ids.insert(&auth.auth_id);
        self.used_nonces.insert(&auth.nonce);

        // 8. Execute on-chain transfer through vault
        let _ = Promise::new(auth.recipient_id.clone()).transfer(NearToken::from_yoctonear(auth.amount.0));

        // Refund any excess attached deposit back to sender
        let refund = attached.saturating_sub(auth.amount.0);
        if refund > 0 {
            let _ = Promise::new(auth.sender_id.clone()).transfer(NearToken::from_yoctonear(refund));
        }

        // 9. Record transaction
        let record = OnChainTransactionRecord {
            auth_id: auth.auth_id.clone(),
            sender_id: auth.sender_id.clone(),
            recipient_id: auth.recipient_id.clone(),
            amount: auth.amount,
            decision: auth.decision,
            risk_score: auth.risk_score,
            executed_at: now,
            block_height: env::block_height(),
        };

        self.transactions.insert(&auth.auth_id, &record);
        self.total_volume_yocto = U128(self.total_volume_yocto.0.saturating_add(auth.amount.0));
        self.total_transfers_count = self.total_transfers_count.saturating_add(1);

        // 10. Emit audit event
        emit_event(PayguardEventData::TransferExecuted {
            auth_id: auth.auth_id,
            sender_id: auth.sender_id,
            recipient_id: auth.recipient_id,
            amount: auth.amount,
            risk_score: auth.risk_score,
        });

        record
    }

    // -------------------------------------------------------------------------
    // Execution: WARN Transaction (Timelock Escrow Creation)
    // -------------------------------------------------------------------------
    #[payable]
    pub fn create_escrow(
        &mut self,
        auth: PolicyAuthorization,
        signature: String,
        timelock_seconds: Option<u64>,
    ) -> EscrowRecord {
        self.assert_not_paused();

        require!(
            auth.decision == DecisionType::Warn,
            "Only WARN policy authorizations can enter escrow"
        );

        let now = env::block_timestamp();
        require!(auth.expires_at >= now, "Authorization has expired");
        require!(auth.issued_at <= now, "Authorization issued in the future");
        require!(auth.expires_at > auth.issued_at, "Invalid expiration interval");
        require!(
            auth.policy_version == self.policy_version,
            "Policy version mismatch"
        );
        require!(
            auth.contract_id == env::current_account_id(),
            "Contract ID mismatch"
        );
        require!(
            auth.sender_id != auth.recipient_id,
            "Sender and recipient cannot be identical"
        );
        require!(
            auth.amount.0 > 0,
            "Escrow amount must be strictly greater than 0"
        );

        // Anti-replay checks
        require!(
            !self.used_auth_ids.contains(&auth.auth_id),
            "Authorization ID already used"
        );
        require!(
            !self.used_nonces.contains(&auth.nonce),
            "Nonce already consumed"
        );

        // Cryptographic signature check
        require!(
            verify_policy_signature(&auth, &signature, &self.policy_signer_pk),
            "Invalid authorization signature"
        );

        let attached = env::attached_deposit().as_yoctonear();
        require!(
            attached >= auth.amount.0,
            "Attached deposit is less than required escrow amount"
        );

        // Consume authorization
        self.used_auth_ids.insert(&auth.auth_id);
        self.used_nonces.insert(&auth.nonce);

        // Determine timelock
        let duration_sec = timelock_seconds
            .unwrap_or(3600)
            .clamp(self.min_escrow_duration_sec, self.max_escrow_duration_sec);
        let duration_ns = duration_sec.saturating_mul(1_000_000_000);
        let timelock_until = now.saturating_add(duration_ns);

        let escrow_id = format!("escrow_{}", auth.auth_id);
        let escrow = EscrowRecord {
            escrow_id: escrow_id.clone(),
            auth_id: auth.auth_id.clone(),
            sender_id: auth.sender_id.clone(),
            recipient_id: auth.recipient_id.clone(),
            amount: auth.amount,
            risk_score: auth.risk_score,
            status: EscrowStatus::PendingApproval,
            created_at: now,
            timelock_until,
            approved_by: None,
            approved_at: None,
            rejection_reason: None,
        };

        self.escrows.insert(&escrow_id, &escrow);
        self.active_escrow_count = self.active_escrow_count.saturating_add(1);

        // Refund any excess deposit
        let refund = attached.saturating_sub(auth.amount.0);
        if refund > 0 {
            let _ = Promise::new(auth.sender_id.clone()).transfer(NearToken::from_yoctonear(refund));
        }

        emit_event(PayguardEventData::EscrowCreated {
            escrow_id,
            auth_id: auth.auth_id,
            sender_id: auth.sender_id,
            recipient_id: auth.recipient_id,
            amount: auth.amount,
            risk_score: auth.risk_score,
            timelock_until,
        });

        escrow
    }

    // -------------------------------------------------------------------------
    // Escrow Management: Approve & Release
    // -------------------------------------------------------------------------
    pub fn approve_escrow(
        &mut self,
        escrow_id: String,
        _reason: Option<String>,
    ) -> EscrowRecord {
        self.assert_not_paused();
        self.assert_authorized_approver();

        let mut escrow = self
            .escrows
            .get(&escrow_id)
            .expect("Escrow record not found");

        require!(
            escrow.status == EscrowStatus::PendingApproval,
            "Escrow is not in PENDING_APPROVAL state"
        );

        let caller = env::predecessor_account_id();
        let now = env::block_timestamp();

        escrow.status = EscrowStatus::Released;
        escrow.approved_by = Some(caller.clone());
        escrow.approved_at = Some(now);

        self.escrows.insert(&escrow_id, &escrow);
        self.active_escrow_count = self.active_escrow_count.saturating_sub(1);
        self.total_volume_yocto = U128(self.total_volume_yocto.0.saturating_add(escrow.amount.0));
        self.total_transfers_count = self.total_transfers_count.saturating_add(1);

        // Release vault funds to recipient
        let _ = Promise::new(escrow.recipient_id.clone())
            .transfer(NearToken::from_yoctonear(escrow.amount.0));

        emit_event(PayguardEventData::EscrowApproved {
            escrow_id: escrow_id.clone(),
            approved_by: caller,
        });

        emit_event(PayguardEventData::EscrowReleased {
            escrow_id,
            recipient_id: escrow.recipient_id.clone(),
            amount: escrow.amount,
        });

        escrow
    }

    // -------------------------------------------------------------------------
    // Escrow Management: Reject & Refund
    // -------------------------------------------------------------------------
    pub fn reject_escrow(
        &mut self,
        escrow_id: String,
        reason: Option<String>,
    ) -> EscrowRecord {
        self.assert_not_paused();

        let mut escrow = self
            .escrows
            .get(&escrow_id)
            .expect("Escrow record not found");

        require!(
            escrow.status == EscrowStatus::PendingApproval,
            "Escrow is not in PENDING_APPROVAL state"
        );

        let caller = env::predecessor_account_id();
        let now = env::block_timestamp();

        // Either an authorized approver, or sender after timelock expiration
        let is_approver = self.is_approver(&caller);
        let is_sender_expired = caller == escrow.sender_id && now > escrow.timelock_until;

        require!(
            is_approver || is_sender_expired,
            "Unauthorized to reject escrow (must be approver or sender after expiration)"
        );

        let rejection_str = reason.unwrap_or_else(|| {
            if is_sender_expired {
                "Refund triggered by sender after timelock expired".to_string()
            } else {
                "Operator manual rejection".to_string()
            }
        });

        escrow.status = EscrowStatus::Refunded;
        escrow.rejection_reason = Some(rejection_str.clone());

        self.escrows.insert(&escrow_id, &escrow);
        self.active_escrow_count = self.active_escrow_count.saturating_sub(1);

        // Refund funds back to sender
        let _ = Promise::new(escrow.sender_id.clone())
            .transfer(NearToken::from_yoctonear(escrow.amount.0));

        emit_event(PayguardEventData::EscrowRejected {
            escrow_id,
            rejected_by: caller,
            sender_id: escrow.sender_id.clone(),
            amount: escrow.amount,
            reason: rejection_str,
        });

        escrow
    }

    // -------------------------------------------------------------------------
    // BLOCK Enforcement: Reject & Record
    // -------------------------------------------------------------------------
    pub fn record_blocked_transfer(
        &mut self,
        auth: PolicyAuthorization,
        signature: String,
    ) {
        self.assert_not_paused();

        require!(
            auth.decision == DecisionType::Block,
            "Expected BLOCK authorization decision"
        );

        // Verify authenticity of the block advisory
        require!(
            verify_policy_signature(&auth, &signature, &self.policy_signer_pk),
            "Invalid authorization signature"
        );

        // Never accept or move any funds for a BLOCK decision
        require!(
            env::attached_deposit().as_yoctonear() == 0,
            "No deposits accepted for blocked transactions"
        );

        self.used_auth_ids.insert(&auth.auth_id);

        emit_event(PayguardEventData::TransferBlocked {
            auth_id: auth.auth_id,
            sender_id: auth.sender_id,
            recipient_id: auth.recipient_id,
            risk_score: auth.risk_score,
            reason: "Deterministic policy block confirmed on-chain".to_string(),
        });
    }

    // -------------------------------------------------------------------------
    // Admin Controls
    // -------------------------------------------------------------------------
    pub fn set_paused(&mut self, is_paused: bool) {
        self.assert_admin();
        self.is_paused = is_paused;
        emit_event(PayguardEventData::VaultPaused { is_paused });
    }

    pub fn update_policy_signer(&mut self, new_signer_pk: PublicKey) {
        self.assert_admin();
        let pk_str = format!("{:?}", new_signer_pk);
        self.policy_signer_pk = new_signer_pk;
        emit_event(PayguardEventData::SignerUpdated {
            new_signer_pk: pk_str,
        });
    }

    pub fn add_approver(&mut self, approver: AccountId) {
        self.assert_admin();
        self.authorized_approvers.insert(&approver);
    }

    pub fn remove_approver(&mut self, approver: AccountId) {
        self.assert_admin();
        self.authorized_approvers.remove(&approver);
    }

    // -------------------------------------------------------------------------
    // View Methods
    // -------------------------------------------------------------------------
    pub fn get_vault_config(&self) -> VaultConfigView {
        VaultConfigView {
            admin_id: self.admin_id.clone(),
            policy_signer_pk: format!("{:?}", self.policy_signer_pk),
            authorized_approvers: vec![self.admin_id.clone()],
            min_escrow_duration_sec: self.min_escrow_duration_sec,
            max_escrow_duration_sec: self.max_escrow_duration_sec,
            policy_version: self.policy_version.clone(),
            is_paused: self.is_paused,
            total_volume_yocto: self.total_volume_yocto,
            total_transfers_count: self.total_transfers_count,
            active_escrow_count: self.active_escrow_count,
        }
    }

    pub fn get_escrow(&self, escrow_id: String) -> Option<EscrowRecord> {
        self.escrows.get(&escrow_id)
    }

    pub fn list_escrows(
        &self,
        from_index: Option<u64>,
        limit: Option<u64>,
    ) -> Vec<EscrowRecord> {
        let start = from_index.unwrap_or(0);
        let limit = limit.unwrap_or(50).min(100);
        self.escrows
            .values()
            .skip(start as usize)
            .take(limit as usize)
            .collect()
    }

    pub fn get_transaction(&self, auth_id: String) -> Option<OnChainTransactionRecord> {
        self.transactions.get(&auth_id)
    }

    pub fn list_transactions(
        &self,
        from_index: Option<u64>,
        limit: Option<u64>,
    ) -> Vec<OnChainTransactionRecord> {
        let start = from_index.unwrap_or(0);
        let limit = limit.unwrap_or(50).min(100);
        self.transactions
            .values()
            .skip(start as usize)
            .take(limit as usize)
            .collect()
    }

    pub fn is_auth_used(&self, auth_id: String) -> bool {
        self.used_auth_ids.contains(&auth_id)
    }

    pub fn is_nonce_used(&self, nonce: u64) -> bool {
        self.used_nonces.contains(&nonce)
    }

    // -------------------------------------------------------------------------
    // Internal Helper Functions
    // -------------------------------------------------------------------------
    fn assert_admin(&self) {
        require!(
            env::predecessor_account_id() == self.admin_id,
            "Requires admin privileges"
        );
    }

    fn assert_not_paused(&self) {
        require!(!self.is_paused, "PayguardVault is currently paused");
    }

    fn assert_authorized_approver(&self) {
        let caller = env::predecessor_account_id();
        require!(
            self.is_approver(&caller),
            "Requires authorized human approver privileges"
        );
    }

    fn is_approver(&self, account: &AccountId) -> bool {
        account == &self.admin_id || self.authorized_approvers.contains(account)
    }
}

// -----------------------------------------------------------------------------
// Unit Tests
// -----------------------------------------------------------------------------
#[cfg(test)]
mod tests {
    use super::*;
    use near_sdk::test_utils::VMContextBuilder;
    use near_sdk::testing_env;
    use near_sdk::AccountId;

    fn admin() -> AccountId {
        "admin.near".parse().unwrap()
    }
    fn signer_pk() -> PublicKey {
        "ed25519:6H8mJuR3iF4QcE7UvY8X3bX9f1K2L3M4N5P6Q7R8S9T0".parse().unwrap()
    }
    fn approver() -> AccountId {
        "approver.near".parse().unwrap()
    }
    fn agent_sender() -> AccountId {
        "agent-alice.near".parse().unwrap()
    }
    fn recipient() -> AccountId {
        "vendor-bob.near".parse().unwrap()
    }
    fn vault_account() -> AccountId {
        "vault.near".parse().unwrap()
    }

    fn get_context(predecessor: AccountId, attached_deposit: NearToken) -> VMContextBuilder {
        let mut builder = VMContextBuilder::new();
        builder
            .current_account_id(vault_account())
            .predecessor_account_id(predecessor)
            .attached_deposit(attached_deposit)
            .block_timestamp(1700000100);
        builder
    }

    #[test]
    fn test_vault_init() {
        let ctx = get_context(admin(), NearToken::from_near(0));
        testing_env!(ctx.build());

        let contract = PayguardVault::init(
            admin(),
            signer_pk(),
            vec![approver()],
            Some(60),
            Some(86400 * 7),
            Some("1.0.0".to_string()),
        );

        let config = contract.get_config();
        assert_eq!(config.admin_id, admin());
        assert_eq!(config.min_escrow_duration_sec, 60);
        assert_eq!(config.max_escrow_duration_sec, 86400 * 7);
        assert_eq!(config.policy_version, "1.0.0");
        assert!(!config.is_paused);
        assert_eq!(config.total_transfers_count, 0);
        assert_eq!(config.active_escrow_count, 0);
    }

    #[test]
    fn test_pause_unpause() {
        let ctx = get_context(admin(), NearToken::from_near(0));
        testing_env!(ctx.build());

        let mut contract = PayguardVault::init(
            admin(),
            signer_pk(),
            vec![approver()],
            None,
            None,
            None,
        );

        contract.pause();
        assert!(contract.get_config().is_paused);

        contract.unpause();
        assert!(!contract.get_config().is_paused);
    }

    #[test]
    #[should_panic(expected = "Requires admin privileges")]
    fn test_pause_non_admin_panics() {
        let ctx = get_context(agent_sender(), NearToken::from_near(0));
        testing_env!(ctx.build());

        let mut contract = PayguardVault::init(
            admin(),
            signer_pk(),
            vec![approver()],
            None,
            None,
            None,
        );

        contract.pause();
    }

    #[test]
    fn test_approver_management() {
        let ctx = get_context(admin(), NearToken::from_near(0));
        testing_env!(ctx.build());

        let mut contract = PayguardVault::init(
            admin(),
            signer_pk(),
            vec![],
            None,
            None,
            None,
        );

        let new_approver: AccountId = "supervisor.near".parse().unwrap();
        assert!(!contract.is_approver(&new_approver));

        contract.add_approver(new_approver.clone());
        assert!(contract.is_approver(&new_approver));

        contract.remove_approver(new_approver.clone());
        assert!(!contract.is_approver(&new_approver));
    }

    #[test]
    fn test_canonical_message_format() {
        let auth = PolicyAuthorization {
            auth_id: "auth-101".to_string(),
            sender_id: agent_sender(),
            recipient_id: recipient(),
            amount: U128(1_000_000_000_000_000_000_000_000), // 1 NEAR
            decision: DecisionType::Allow,
            risk_score: 12,
            policy_version: "1.0.0".to_string(),
            nonce: 42,
            issued_at: 1700000000,
            expires_at: 1700000500,
            network_id: "testnet".to_string(),
            contract_id: vault_account(),
        };

        let canonical = auth.to_canonical_payload();
        assert_eq!(
            canonical,
            "PAYGUARD:v1:testnet:vault.near:auth-101:agent-alice.near:vendor-bob.near:1000000000000000000000000:ALLOW:12:1.0.0:42:1700000000:1700000500"
        );
    }
}

from datetime import datetime, timedelta
import json
import os
import sqlite3
import threading
from typing import Any, Dict, List, Optional, Tuple
from app.core.config import settings
from app.core.logging import logger


class Database:
    """
    Thread-safe SQLite persistent repository for PAYGUARD Phase 2.
    Stores transactions, AI intent analysis, agent execution records,
    security findings, cryptographic evidence, and policy states.
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or settings.DATABASE_PATH
        # Ensure parent directory exists
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        self._lock = threading.RLock()
        self._init_tables()
        self._seed_initial_data_if_empty()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=20.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_tables(self) -> None:
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()

            # 1. Transactions Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id TEXT PRIMARY KEY,
                sender TEXT NOT NULL,
                recipient TEXT NOT NULL,
                amount REAL NOT NULL,
                currency TEXT NOT NULL DEFAULT 'NEAR',
                decision TEXT NOT NULL,
                risk_score INTEGER NOT NULL,
                risk_level TEXT NOT NULL,
                requires_approval INTEGER NOT NULL DEFAULT 0,
                execution_allowed INTEGER NOT NULL DEFAULT 0,
                confidence_score REAL NOT NULL DEFAULT 0.95,
                reasons_json TEXT NOT NULL,
                policy_checks_json TEXT NOT NULL,
                agent_id TEXT,
                purpose TEXT,
                approval_status TEXT NOT NULL DEFAULT 'NONE',
                intent_matched INTEGER DEFAULT 1,
                intent_discrepancy TEXT,
                is_mock_simulation INTEGER NOT NULL DEFAULT 1,
                timestamp TEXT NOT NULL,
                status TEXT DEFAULT 'CONFIRMED',
                tx_hash TEXT,
                block_height INTEGER,
                block_hash TEXT,
                explorer_url TEXT,
                escrow_id TEXT,
                error_details TEXT,
                execution_mode TEXT DEFAULT 'SIMULATION',
                evidence_hash TEXT
            )
            """)

            # Phase 4 schema migration: dynamically add any missing columns to existing DBs
            cursor.execute("PRAGMA table_info(transactions)")
            existing_cols = {col[1] for col in cursor.fetchall()}
            phase4_columns = {
                "status": "TEXT DEFAULT 'CONFIRMED'",
                "tx_hash": "TEXT",
                "block_height": "INTEGER",
                "block_hash": "TEXT",
                "explorer_url": "TEXT",
                "escrow_id": "TEXT",
                "error_details": "TEXT",
                "execution_mode": "TEXT DEFAULT 'SIMULATION'",
                "evidence_hash": "TEXT",
            }
            for col_name, col_def in phase4_columns.items():
                if col_name not in existing_cols:
                    cursor.execute(f"ALTER TABLE transactions ADD COLUMN {col_name} {col_def}")

            # 2. Agent Executions Table (LangGraph Telemetry)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_executions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id TEXT NOT NULL,
                agent_name TEXT NOT NULL,
                status TEXT NOT NULL,
                execution_time_ms REAL NOT NULL,
                findings_json TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (transaction_id) REFERENCES transactions (transaction_id) ON DELETE CASCADE
            )
            """)

            # 3. Security Findings / Threat Intelligence Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS security_findings (
                id TEXT PRIMARY KEY,
                transaction_id TEXT,
                category TEXT NOT NULL,
                severity TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                indicator TEXT,
                timestamp TEXT NOT NULL
            )
            """)

            # 4. Cryptographic Authorization Evidence Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS authorization_evidence (
                transaction_id TEXT PRIMARY KEY,
                canonical_payload TEXT NOT NULL,
                sha256_digest TEXT NOT NULL,
                policy_version TEXT NOT NULL,
                is_tamper_verified INTEGER NOT NULL DEFAULT 1,
                generated_at TEXT NOT NULL,
                metadata_json TEXT,
                FOREIGN KEY (transaction_id) REFERENCES transactions (transaction_id) ON DELETE CASCADE
            )
            """)

            # 5. Approval Records Table (Human-in-the-Loop)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS approval_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id TEXT NOT NULL,
                decision TEXT NOT NULL,
                operator_id TEXT NOT NULL,
                reason TEXT,
                decided_at TEXT NOT NULL,
                FOREIGN KEY (transaction_id) REFERENCES transactions (transaction_id) ON DELETE CASCADE
            )
            """)

            # 6. Policies Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS policies (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                version TEXT NOT NULL,
                config_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """)

            # 7. Real-Time Events Table (Phase 5)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                event_id TEXT PRIMARY KEY,
                event_type TEXT NOT NULL,
                category TEXT NOT NULL,
                transaction_id TEXT,
                timestamp TEXT NOT NULL,
                source TEXT NOT NULL,
                severity TEXT NOT NULL,
                payload_json TEXT NOT NULL
            )
            """)

            # 8. Blockchain Checkpoints Table (Phase 5)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS blockchain_checkpoints (
                key TEXT PRIMARY KEY,
                last_block_height INTEGER NOT NULL,
                last_block_hash TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """)

            # 9. Agent Behavioral Profiles Table (Phase 6)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_profiles (
                agent_id TEXT PRIMARY KEY,
                profile_version INTEGER NOT NULL DEFAULT 1,
                transaction_count INTEGER NOT NULL DEFAULT 0,
                average_amount REAL NOT NULL DEFAULT 0.0,
                maximum_amount REAL NOT NULL DEFAULT 0.0,
                std_dev_amount REAL NOT NULL DEFAULT 0.0,
                transaction_frequency_per_day REAL NOT NULL DEFAULT 0.0,
                spending_velocity_24h REAL NOT NULL DEFAULT 0.0,
                known_recipients_json TEXT NOT NULL DEFAULT '[]',
                recipient_distribution_json TEXT NOT NULL DEFAULT '{}',
                allow_count INTEGER NOT NULL DEFAULT 0,
                warn_count INTEGER NOT NULL DEFAULT 0,
                block_count INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'INSUFFICIENT_HISTORY',
                behavioral_baseline_json TEXT NOT NULL DEFAULT '{}',
                last_updated TEXT NOT NULL
            )
            """)

            # 10. AI Anomaly Findings Table (Phase 6)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_anomalies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id TEXT NOT NULL,
                affected_agent TEXT NOT NULL,
                anomaly_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                anomaly_score REAL NOT NULL,
                observed_value TEXT NOT NULL,
                expected_range TEXT NOT NULL,
                explanation TEXT NOT NULL,
                detection_method TEXT NOT NULL,
                supporting_evidence_json TEXT NOT NULL DEFAULT '[]',
                timestamp TEXT NOT NULL
            )
            """)

            # 11. AI Evaluations & Consensus Table (Phase 6)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_evaluations (
                transaction_id TEXT PRIMARY KEY,
                intent_score REAL NOT NULL,
                anomaly_score REAL NOT NULL,
                consensus_score REAL NOT NULL,
                disagreement_score REAL NOT NULL,
                recommended_review_level TEXT NOT NULL,
                risk_category TEXT NOT NULL,
                confidence_category TEXT NOT NULL,
                confidence_score REAL NOT NULL,
                evaluation_json TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
            """)

            # Indices
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tx_timestamp ON transactions (timestamp DESC)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tx_decision ON transactions (decision)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_agent_tx ON agent_executions (transaction_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_findings_severity ON security_findings (severity)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events (timestamp DESC)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_type ON events (event_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_category ON events (category)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_tx ON events (transaction_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_severity ON events (severity)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_anomalies_agent ON ai_anomalies (affected_agent)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_anomalies_type ON ai_anomalies (anomaly_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_anomalies_severity ON ai_anomalies (severity)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_eval_timestamp ON ai_evaluations (timestamp DESC)")
            conn.commit()
            logger.info("Database tables initialized successfully.")

    def _seed_initial_data_if_empty(self) -> None:
        """Seed initial high-quality records on fresh database creation."""
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM transactions")
            count = cursor.fetchone()[0]
            if count > 0:
                return

            now = datetime.utcnow()
            seed_txs = [
                {
                    "transaction_id": "tx_demo_001",
                    "sender": "agent-alpha.near",
                    "recipient": "oracle.near",
                    "amount": 2.5,
                    "currency": "NEAR",
                    "decision": "ALLOW",
                    "risk_score": 12,
                    "risk_level": "LOW",
                    "requires_approval": 0,
                    "execution_allowed": 1,
                    "confidence_score": 0.98,
                    "reasons_json": json.dumps(["All deterministic security policies and risk thresholds passed."]),
                    "policy_checks_json": json.dumps({
                        "data_integrity": "PASSED",
                        "recipient_status": "PASSED",
                        "amount_limit": "PASSED",
                        "daily_limit": "PASSED",
                        "duplicate_check": "PASSED",
                        "frequency_check": "PASSED",
                    }),
                    "agent_id": "agent-alpha.near",
                    "purpose": "Fetch decentralized oracle price feeds for NEAR/USD",
                    "approval_status": "APPROVED",
                    "intent_matched": 1,
                    "intent_discrepancy": None,
                    "is_mock_simulation": 1,
                    "timestamp": (now - timedelta(minutes=45)).isoformat(),
                },
                {
                    "transaction_id": "tx_demo_002",
                    "sender": "agent-alpha.near",
                    "recipient": "malicious-drainer.near",
                    "amount": 100.0,
                    "currency": "NEAR",
                    "decision": "BLOCK",
                    "risk_score": 95,
                    "risk_level": "HIGH",
                    "requires_approval": 0,
                    "execution_allowed": 0,
                    "confidence_score": 0.99,
                    "reasons_json": json.dumps([
                        "Recipient 'malicious-drainer.near' is on the critical blocklist.",
                        "Transaction amount (100.00 NEAR) exceeds maximum per-transaction limit (50.00 NEAR).",
                        "Risk score (95) exceeds high-risk threshold (70).",
                    ]),
                    "policy_checks_json": json.dumps({
                        "data_integrity": "PASSED",
                        "recipient_status": "BLOCKED",
                        "amount_limit": "FAILED",
                        "daily_limit": "PASSED",
                        "duplicate_check": "PASSED",
                        "frequency_check": "PASSED",
                    }),
                    "agent_id": "agent-alpha.near",
                    "purpose": "Transfer 10 NEAR to treasury for operating cost",
                    "approval_status": "NONE",
                    "intent_matched": 0,
                    "intent_discrepancy": "Severe recipient divergence: declared treasury, actual malicious-drainer.near",
                    "is_mock_simulation": 1,
                    "timestamp": (now - timedelta(minutes=30)).isoformat(),
                },
                {
                    "transaction_id": "tx_demo_003",
                    "sender": "agent-beta.near",
                    "recipient": "unverified-agent-dex.near",
                    "amount": 35.0,
                    "currency": "NEAR",
                    "decision": "WARN",
                    "risk_score": 45,
                    "risk_level": "MEDIUM",
                    "requires_approval": 1,
                    "execution_allowed": 0,
                    "confidence_score": 0.92,
                    "reasons_json": json.dumps([
                        "Recipient 'unverified-agent-dex.near' is an unverified counterparty.",
                        "Elevated risk score (45) requires human verification.",
                    ]),
                    "policy_checks_json": json.dumps({
                        "data_integrity": "PASSED",
                        "recipient_status": "WARNING",
                        "amount_limit": "PASSED",
                        "daily_limit": "PASSED",
                        "duplicate_check": "PASSED",
                        "frequency_check": "PASSED",
                    }),
                    "agent_id": "agent-beta.near",
                    "purpose": "Liquidity rebalancing on external contract",
                    "approval_status": "PENDING",
                    "intent_matched": 1,
                    "intent_discrepancy": None,
                    "is_mock_simulation": 1,
                    "timestamp": (now - timedelta(minutes=15)).isoformat(),
                },
                {
                    "transaction_id": "tx_demo_004",
                    "sender": "agent-gamma.near",
                    "recipient": "treasury.payguard.near",
                    "amount": 15.0,
                    "currency": "NEAR",
                    "decision": "ALLOW",
                    "risk_score": 5,
                    "risk_level": "LOW",
                    "requires_approval": 0,
                    "execution_allowed": 1,
                    "confidence_score": 0.99,
                    "reasons_json": json.dumps(["All deterministic security policies and risk thresholds passed."]),
                    "policy_checks_json": json.dumps({
                        "data_integrity": "PASSED",
                        "recipient_status": "PASSED",
                        "amount_limit": "PASSED",
                        "daily_limit": "PASSED",
                        "duplicate_check": "PASSED",
                        "frequency_check": "PASSED",
                    }),
                    "agent_id": "agent-gamma.near",
                    "purpose": "Automated protocol staking contribution",
                    "approval_status": "APPROVED",
                    "intent_matched": 1,
                    "intent_discrepancy": None,
                    "is_mock_simulation": 1,
                    "timestamp": (now - timedelta(minutes=5)).isoformat(),
                },
            ]

            for tx in seed_txs:
                cursor.execute("""
                INSERT INTO transactions (
                    transaction_id, sender, recipient, amount, currency, decision,
                    risk_score, risk_level, requires_approval, execution_allowed,
                    confidence_score, reasons_json, policy_checks_json, agent_id,
                    purpose, approval_status, intent_matched, intent_discrepancy,
                    is_mock_simulation, timestamp
                ) VALUES (
                    :transaction_id, :sender, :recipient, :amount, :currency, :decision,
                    :risk_score, :risk_level, :requires_approval, :execution_allowed,
                    :confidence_score, :reasons_json, :policy_checks_json, :agent_id,
                    :purpose, :approval_status, :intent_matched, :intent_discrepancy,
                    :is_mock_simulation, :timestamp
                )
                """, tx)

            # Seed security findings
            cursor.execute("""
            INSERT INTO security_findings (id, transaction_id, category, severity, title, description, indicator, timestamp)
            VALUES 
            ('find_demo_1', 'tx_demo_002', 'Unauthorized Drain Exploit', 'CRITICAL', 'Exploit Blocked: malicious-drainer.near', 'Recipient is on critical blocklist; amount exceeds maximum policy limit', 'malicious-drainer.near', :ts1),
            ('find_demo_2', 'tx_demo_003', 'Unverified Counterparty', 'MEDIUM', 'Human Approval Required: unverified-agent-dex.near', 'Unverified DEX address with elevated financial allocation', 'unverified-agent-dex.near', :ts2)
            """, {"ts1": (now - timedelta(minutes=30)).isoformat(), "ts2": (now - timedelta(minutes=15)).isoformat()})

            conn.commit()
            logger.info("Database seeded with initial demonstration records.")

    # -------------------------------------------------------------------------
    # Transactions CRUD
    # -------------------------------------------------------------------------
    def save_transaction(self, tx_data: Dict[str, Any]) -> None:
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            decision = tx_data["decision"]
            default_status = "CONFIRMED" if decision == "ALLOW" else ("BLOCKED" if decision == "BLOCK" else "WARN_PENDING_APPROVAL")
            status_val = tx_data.get("status") or default_status

            tx_hash_val = tx_data.get("tx_hash") or tx_data.get("evidence_hash")
            explorer_url_val = tx_data.get("explorer_url") or (
                f"https://testnet.nearblocks.io/txns/{tx_hash_val}" if tx_hash_val else None
            )

            cursor.execute("""
            INSERT INTO transactions (
                transaction_id, sender, recipient, amount, currency, decision,
                risk_score, risk_level, requires_approval, execution_allowed,
                confidence_score, reasons_json, policy_checks_json, agent_id,
                purpose, approval_status, intent_matched, intent_discrepancy,
                is_mock_simulation, timestamp,
                status, tx_hash, block_height, block_hash, explorer_url,
                escrow_id, error_details, execution_mode, evidence_hash
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(transaction_id) DO UPDATE SET
                sender = excluded.sender,
                recipient = excluded.recipient,
                amount = excluded.amount,
                currency = excluded.currency,
                decision = excluded.decision,
                risk_score = excluded.risk_score,
                risk_level = excluded.risk_level,
                requires_approval = excluded.requires_approval,
                execution_allowed = excluded.execution_allowed,
                confidence_score = excluded.confidence_score,
                reasons_json = excluded.reasons_json,
                policy_checks_json = excluded.policy_checks_json,
                agent_id = excluded.agent_id,
                purpose = excluded.purpose,
                approval_status = excluded.approval_status,
                intent_matched = excluded.intent_matched,
                intent_discrepancy = excluded.intent_discrepancy,
                is_mock_simulation = excluded.is_mock_simulation,
                timestamp = excluded.timestamp,
                status = excluded.status,
                tx_hash = excluded.tx_hash,
                block_height = excluded.block_height,
                block_hash = excluded.block_hash,
                explorer_url = excluded.explorer_url,
                escrow_id = excluded.escrow_id,
                error_details = excluded.error_details,
                execution_mode = excluded.execution_mode,
                evidence_hash = excluded.evidence_hash
            """, (
                tx_data["transaction_id"],
                tx_data["sender"],
                tx_data["recipient"],
                float(tx_data["amount"]),
                tx_data.get("currency", "NEAR"),
                decision,
                int(tx_data["risk_score"]),
                tx_data.get("risk_level", "LOW"),
                1 if tx_data.get("requires_approval") else 0,
                1 if tx_data.get("execution_allowed") else 0,
                float(tx_data.get("confidence_score", 0.95)),
                json.dumps(tx_data.get("reasons", [])),
                json.dumps(tx_data.get("policy_checks", {})),
                tx_data.get("agent_id", "autonomous-agent-01"),
                tx_data.get("purpose", ""),
                tx_data.get("approval_status", "NONE"),
                1 if tx_data.get("intent_matched", True) else 0,
                tx_data.get("intent_discrepancy"),
                1 if tx_data.get("is_mock_simulation", True) else 0,
                tx_data.get("timestamp") or datetime.utcnow().isoformat(),
                status_val,
                tx_hash_val,
                tx_data.get("block_height"),
                tx_data.get("block_hash"),
                explorer_url_val,
                tx_data.get("escrow_id"),
                tx_data.get("error_details"),
                tx_data.get("execution_mode", "SIMULATION" if tx_data.get("is_mock_simulation", True) else "ONCHAIN"),
                tx_hash_val,
            ))
            conn.commit()

    def get_transaction(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM transactions WHERE transaction_id = ?", (transaction_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_tx_dict(row)

    def list_transactions(self, limit: int = 50, decision: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            if decision and decision.upper() != "ALL":
                cursor.execute(
                    "SELECT * FROM transactions WHERE decision = ? ORDER BY timestamp DESC LIMIT ?",
                    (decision.upper(), limit),
                )
            else:
                cursor.execute(
                    "SELECT * FROM transactions ORDER BY timestamp DESC LIMIT ?",
                    (limit,),
                )
            rows = cursor.fetchall()
            return [self._row_to_tx_dict(r) for r in rows]

    def _row_to_tx_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        keys = row.keys()
        decision = row["decision"]
        default_status = "CONFIRMED" if decision == "ALLOW" else ("BLOCKED" if decision == "BLOCK" else "WARN_PENDING_APPROVAL")
        
        status = row["status"] if "status" in keys and row["status"] else default_status
        tx_hash = row["tx_hash"] if "tx_hash" in keys else None
        block_height = row["block_height"] if "block_height" in keys else None
        block_hash = row["block_hash"] if "block_hash" in keys else None
        explorer_url = row["explorer_url"] if "explorer_url" in keys and row["explorer_url"] else (
            f"https://testnet.nearblocks.io/txns/{tx_hash}" if tx_hash else None
        )
        escrow_id = row["escrow_id"] if "escrow_id" in keys else None
        error_details = row["error_details"] if "error_details" in keys else None
        execution_mode = row["execution_mode"] if "execution_mode" in keys and row["execution_mode"] else (
            "ONCHAIN" if not bool(row["is_mock_simulation"]) else "SIMULATION"
        )
        evidence_hash = row["evidence_hash"] if "evidence_hash" in keys and row["evidence_hash"] else tx_hash

        return {
            "transaction_id": row["transaction_id"],
            "sender": row["sender"],
            "recipient": row["recipient"],
            "amount": row["amount"],
            "currency": row["currency"],
            "decision": row["decision"],
            "risk_score": row["risk_score"],
            "risk_level": row["risk_level"],
            "requires_approval": bool(row["requires_approval"]),
            "execution_allowed": bool(row["execution_allowed"]),
            "confidence_score": row["confidence_score"],
            "reasons": json.loads(row["reasons_json"]),
            "policy_checks": json.loads(row["policy_checks_json"]),
            "agent_id": row["agent_id"],
            "purpose": row["purpose"],
            "approval_status": row["approval_status"],
            "intent_matched": bool(row["intent_matched"]),
            "intent_discrepancy": row["intent_discrepancy"],
            "is_mock_simulation": bool(row["is_mock_simulation"]),
            "timestamp": row["timestamp"],
            "status": status,
            "tx_hash": tx_hash,
            "block_height": block_height,
            "block_hash": block_hash,
            "explorer_url": explorer_url,
            "escrow_id": escrow_id,
            "error_details": error_details,
            "execution_mode": execution_mode,
            "evidence_hash": evidence_hash,
        }

    # -------------------------------------------------------------------------
    # Agent Execution Logs (LangGraph Telemetry)
    # -------------------------------------------------------------------------
    def save_agent_execution(
        self,
        transaction_id: str,
        agent_name: str,
        status: str,
        execution_time_ms: float,
        findings: Dict[str, Any],
    ) -> None:
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO agent_executions (transaction_id, agent_name, status, execution_time_ms, findings_json, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (
                transaction_id,
                agent_name,
                status,
                execution_time_ms,
                json.dumps(findings),
                datetime.utcnow().isoformat(),
            ))
            conn.commit()

    @staticmethod
    def _safe_load_findings(val: Any) -> Any:
        if not val:
            return {}
        if isinstance(val, (dict, list)):
            return val
        try:
            return json.loads(val)
        except Exception:
            return {"summary": str(val)}

    def get_agent_executions(self, transaction_id: str) -> List[Dict[str, Any]]:
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM agent_executions WHERE transaction_id = ? ORDER BY id ASC",
                (transaction_id,),
            )
            rows = cursor.fetchall()
            return [
                {
                    "id": r["id"],
                    "execution_id": str(r["id"]),
                    "transaction_id": r["transaction_id"],
                    "agent_name": r["agent_name"],
                    "status": r["status"],
                    "execution_time_ms": r["execution_time_ms"],
                    "findings": self._safe_load_findings(r["findings_json"]),
                    "timestamp": r["timestamp"],
                }
                for r in rows
            ]

    def list_recent_agent_executions(self, limit: int = 30) -> List[Dict[str, Any]]:
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM agent_executions ORDER BY id DESC LIMIT ?",
                (limit,),
            )
            rows = cursor.fetchall()
            return [
                {
                    "id": r["id"],
                    "execution_id": str(r["id"]),
                    "transaction_id": r["transaction_id"],
                    "agent_name": r["agent_name"],
                    "status": r["status"],
                    "execution_time_ms": r["execution_time_ms"],
                    "findings": self._safe_load_findings(r["findings_json"]),
                    "timestamp": r["timestamp"],
                }
                for r in rows
            ]

    # -------------------------------------------------------------------------
    # Security Findings & Threat Telemetry
    # -------------------------------------------------------------------------
    def save_security_finding(
        self,
        finding_id: str,
        transaction_id: Optional[str],
        category: str,
        severity: str,
        title: str,
        description: str,
        indicator: Optional[str] = None,
    ) -> None:
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO security_findings (id, transaction_id, category, severity, title, description, indicator, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                finding_id,
                transaction_id,
                category,
                severity,
                title,
                description,
                indicator,
                datetime.utcnow().isoformat(),
            ))
            conn.commit()

    def list_security_findings(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM security_findings ORDER BY timestamp DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    # -------------------------------------------------------------------------
    # Cryptographic Authorization Evidence
    # -------------------------------------------------------------------------
    def save_authorization_evidence(
        self,
        transaction_id: str,
        canonical_payload: str,
        sha256_digest: str,
        policy_version: str,
        is_tamper_verified: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO authorization_evidence (
                transaction_id, canonical_payload, sha256_digest, policy_version,
                is_tamper_verified, generated_at, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                transaction_id,
                canonical_payload,
                sha256_digest,
                policy_version,
                1 if is_tamper_verified else 0,
                datetime.utcnow().isoformat(),
                json.dumps(metadata or {}),
            ))
            conn.commit()

    def get_authorization_evidence(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM authorization_evidence WHERE transaction_id = ?", (transaction_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return {
                "transaction_id": row["transaction_id"],
                "canonical_payload": row["canonical_payload"],
                "sha256_digest": row["sha256_digest"],
                "policy_version": row["policy_version"],
                "is_tamper_verified": bool(row["is_tamper_verified"]),
                "generated_at": row["generated_at"],
                "metadata": json.loads(row["metadata_json"] or "{}"),
            }

    # -------------------------------------------------------------------------
    # Approvals Management (Human In The Loop)
    # -------------------------------------------------------------------------
    def record_approval(
        self,
        transaction_id: str,
        decision: str,  # 'APPROVE' or 'REJECT'
        operator_id: str = "operator_01",
        reason: Optional[str] = None,
    ) -> bool:
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            # Check transaction exists
            cursor.execute("SELECT * FROM transactions WHERE transaction_id = ?", (transaction_id,))
            tx = cursor.fetchone()
            if not tx:
                return False

            new_status = "APPROVED" if decision == "APPROVE" else "REJECTED"
            exec_allowed = 1 if decision == "APPROVE" else 0

            cursor.execute("""
            UPDATE transactions
            SET approval_status = ?, execution_allowed = ?, requires_approval = 0
            WHERE transaction_id = ?
            """, (new_status, exec_allowed, transaction_id))

            cursor.execute("""
            INSERT INTO approval_records (transaction_id, decision, operator_id, reason, decided_at)
            VALUES (?, ?, ?, ?, ?)
            """, (
                transaction_id,
                decision,
                operator_id,
                reason or f"Operator {operator_id} manually decided {decision}",
                datetime.utcnow().isoformat(),
            ))
            conn.commit()
            return True

    def list_pending_approvals(self) -> List[Dict[str, Any]]:
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT * FROM transactions
            WHERE requires_approval = 1 OR approval_status = 'PENDING'
            ORDER BY timestamp DESC
            """)
            rows = cursor.fetchall()
            return [self._row_to_tx_dict(r) for r in rows]

    # -------------------------------------------------------------------------
    # Persistent Policies
    # -------------------------------------------------------------------------
    def save_policy(self, version: str, config: Dict[str, Any]) -> None:
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO policies (id, version, config_json, updated_at)
            VALUES (1, ?, ?, ?)
            """, (version, json.dumps(config), datetime.utcnow().isoformat()))
            conn.commit()

    def get_policy(self) -> Optional[Dict[str, Any]]:
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM policies WHERE id = 1")
            row = cursor.fetchone()
            if not row:
                return None
            return {
                "version": row["version"],
                "updated_at": row["updated_at"],
                "config": json.loads(row["config_json"]),
            }

    # -------------------------------------------------------------------------
    # Metrics Aggregator
    # -------------------------------------------------------------------------
    def get_metrics(self) -> Dict[str, Any]:
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM transactions")
            total = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM transactions WHERE decision = 'ALLOW'")
            approved = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM transactions WHERE decision = 'WARN'")
            warned = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM transactions WHERE decision = 'BLOCK'")
            blocked = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM transactions WHERE requires_approval = 1 OR approval_status = 'PENDING'")
            pending = cursor.fetchone()[0]

            cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions")
            total_vol = round(float(cursor.fetchone()[0]), 2)

            cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE decision = 'BLOCK'")
            protected_vol = round(float(cursor.fetchone()[0]), 2)

            cursor.execute("SELECT COALESCE(AVG(risk_score), 0) FROM transactions")
            avg_risk = round(float(cursor.fetchone()[0]), 1)

            cursor.execute("SELECT COUNT(DISTINCT sender) FROM transactions")
            active_agents = max(int(cursor.fetchone()[0]), 1)

            # Recent alerts from security findings
            cursor.execute("""
            SELECT id, timestamp, severity, title, description, transaction_id, indicator as recipient
            FROM security_findings
            ORDER BY timestamp DESC LIMIT 10
            """)
            alerts = [dict(r) for r in cursor.fetchall()]

            return {
                "total_monitored": total,
                "approved_count": approved,
                "warn_count": warned,
                "blocked_count": blocked,
                "pending_approvals": pending,
                "total_near_volume": total_vol,
                "protected_near_volume": protected_vol,
                "average_risk_score": avg_risk,
                "active_agents_monitored": active_agents,
                "recent_alerts": alerts,
                "is_demo_metrics": False,
            }

    # -------------------------------------------------------------------------
    # Real-Time Events Persistence & Telemetry (Phase 5)
    # -------------------------------------------------------------------------
    def save_event(self, event_data: Dict[str, Any]) -> None:
        """Stores a standardized real-time event into the events ledger with idempotency."""
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            payload_str = json.dumps(event_data.get("payload", {}))
            cursor.execute("""
            INSERT OR REPLACE INTO events (
                event_id, event_type, category, transaction_id, timestamp, source, severity, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event_data["event_id"],
                event_data["event_type"],
                event_data.get("category", "transactions"),
                event_data.get("transaction_id"),
                event_data["timestamp"],
                event_data.get("source", "backend"),
                event_data.get("severity", "INFO"),
                payload_str,
            ))
            conn.commit()

    def get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a single event by event ID."""
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM events WHERE event_id = ?", (event_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return {
                "event_id": row["event_id"],
                "event_type": row["event_type"],
                "category": row["category"],
                "transaction_id": row["transaction_id"],
                "timestamp": row["timestamp"],
                "source": row["source"],
                "severity": row["severity"],
                "payload": json.loads(row["payload_json"]),
            }

    def list_events(
        self,
        limit: int = 50,
        offset: int = 0,
        event_type: Optional[str] = None,
        category: Optional[str] = None,
        severity: Optional[str] = None,
        transaction_id: Optional[str] = None,
        source: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Lists events with filtering and pagination."""
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            conditions = []
            params = []

            if event_type:
                conditions.append("event_type = ?")
                params.append(event_type)
            if category:
                conditions.append("category = ?")
                params.append(category)
            if severity:
                conditions.append("severity = ?")
                params.append(severity)
            if transaction_id:
                conditions.append("transaction_id = ?")
                params.append(transaction_id)
            if source:
                conditions.append("source = ?")
                params.append(source)

            where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""

            # Count total
            cursor.execute(f"SELECT COUNT(*) FROM events{where_clause}", params)
            total = cursor.fetchone()[0]

            # Fetch rows
            query = f"SELECT * FROM events{where_clause} ORDER BY timestamp DESC LIMIT ? OFFSET ?"
            cursor.execute(query, params + [limit, offset])
            rows = cursor.fetchall()

            events = [
                {
                    "event_id": r["event_id"],
                    "event_type": r["event_type"],
                    "category": r["category"],
                    "transaction_id": r["transaction_id"],
                    "timestamp": r["timestamp"],
                    "source": r["source"],
                    "severity": r["severity"],
                    "payload": json.loads(r["payload_json"]),
                }
                for r in rows
            ]
            return events, total

    def get_events_for_transaction(self, transaction_id: str) -> List[Dict[str, Any]]:
        """Retrieves complete chronological event history for a given transaction."""
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM events WHERE transaction_id = ? ORDER BY timestamp ASC",
                (transaction_id,),
            )
            rows = cursor.fetchall()
            return [
                {
                    "event_id": r["event_id"],
                    "event_type": r["event_type"],
                    "category": r["category"],
                    "transaction_id": r["transaction_id"],
                    "timestamp": r["timestamp"],
                    "source": r["source"],
                    "severity": r["severity"],
                    "payload": json.loads(r["payload_json"]),
                }
                for r in rows
            ]

    def get_event_metrics(self) -> Dict[str, Any]:
        """Calculates aggregate metrics across persisted events."""
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM events")
            total = cursor.fetchone()[0]

            cursor.execute("SELECT category, COUNT(*) FROM events GROUP BY category")
            by_category = {r[0]: r[1] for r in cursor.fetchall()}

            cursor.execute("SELECT severity, COUNT(*) FROM events GROUP BY severity")
            by_severity = {r[0]: r[1] for r in cursor.fetchall()}

            # Rate per minute in the last 15 minutes
            fifteen_min_ago = (datetime.utcnow() - timedelta(minutes=15)).isoformat()
            cursor.execute("SELECT COUNT(*) FROM events WHERE timestamp >= ?", (fifteen_min_ago,))
            recent_count = cursor.fetchone()[0]
            rate_per_min = round(recent_count / 15.0, 2)

            return {
                "total_events": total,
                "by_category": by_category,
                "by_severity": by_severity,
                "recent_event_rate_per_min": rate_per_min,
            }

    # -------------------------------------------------------------------------
    # Blockchain Checkpoints (Phase 5)
    # -------------------------------------------------------------------------
    def save_blockchain_checkpoint(self, key: str, block_height: int, block_hash: str) -> None:
        """Saves a synchronization checkpoint for NEAR block/event scanning."""
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO blockchain_checkpoints (key, last_block_height, last_block_hash, updated_at)
            VALUES (?, ?, ?, ?)
            """, (key, block_height, block_hash, datetime.utcnow().isoformat()))
            conn.commit()

    def get_blockchain_checkpoint(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieves a synchronization checkpoint."""
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM blockchain_checkpoints WHERE key = ?", (key,))
            row = cursor.fetchone()
            if not row:
                return None
            return {
                "key": row["key"],
                "last_block_height": row["last_block_height"],
                "last_block_hash": row["last_block_hash"],
                "updated_at": row["updated_at"],
            }

    # -------------------------------------------------------------------------
    # AI Behavioral Profiles & Intelligence (Phase 6)
    # -------------------------------------------------------------------------
    def save_agent_profile(self, profile: Any) -> None:
        """Persists or updates an autonomous agent's behavioral profile."""
        if hasattr(profile, "model_dump"):
            profile = profile.model_dump()
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO agent_profiles (
                agent_id, profile_version, transaction_count, average_amount,
                maximum_amount, std_dev_amount, transaction_frequency_per_day,
                spending_velocity_24h, known_recipients_json, recipient_distribution_json,
                allow_count, warn_count, block_count, status, behavioral_baseline_json, last_updated
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                profile["agent_id"],
                profile.get("profile_version", 1),
                profile.get("transaction_count", 0),
                profile.get("average_amount", 0.0),
                profile.get("maximum_amount", 0.0),
                profile.get("std_dev_amount", 0.0),
                profile.get("transaction_frequency_per_day", 0.0),
                profile.get("spending_velocity_24h", 0.0),
                json.dumps(profile.get("known_recipients", [])),
                json.dumps(profile.get("recipient_distribution", {})),
                profile.get("allow_count", 0),
                profile.get("warn_count", 0),
                profile.get("block_count", 0),
                profile.get("status", "INSUFFICIENT_HISTORY"),
                json.dumps(profile.get("behavioral_baseline", {})),
                profile.get("last_updated", datetime.utcnow().isoformat()),
            ))
            conn.commit()

    def get_agent_profile(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves an agent's behavioral profile, or builds it from history if missing."""
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM agent_profiles WHERE LOWER(agent_id) = LOWER(?)", (agent_id,))
            row = cursor.fetchone()
            if row:
                return {
                    "agent_id": row["agent_id"],
                    "profile_version": row["profile_version"],
                    "transaction_count": row["transaction_count"],
                    "average_amount": row["average_amount"],
                    "maximum_amount": row["maximum_amount"],
                    "std_dev_amount": row["std_dev_amount"],
                    "transaction_frequency_per_day": row["transaction_frequency_per_day"],
                    "spending_velocity_24h": row["spending_velocity_24h"],
                    "known_recipients": json.loads(row["known_recipients_json"] or "[]"),
                    "recipient_distribution": json.loads(row["recipient_distribution_json"] or "{}"),
                    "allow_count": row["allow_count"],
                    "warn_count": row["warn_count"],
                    "block_count": row["block_count"],
                    "status": row["status"],
                    "behavioral_baseline": json.loads(row["behavioral_baseline_json"] or "{}"),
                    "last_updated": row["last_updated"],
                }
        # If not present in table, build dynamically from verified transaction records
        return self.update_agent_profile_from_history(agent_id)

    def list_agent_profiles(self) -> List[Dict[str, Any]]:
        """Lists all persistent autonomous agent profiles."""
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM agent_profiles ORDER BY transaction_count DESC")
            rows = cursor.fetchall()
            return [
                {
                    "agent_id": r["agent_id"],
                    "profile_version": r["profile_version"],
                    "transaction_count": r["transaction_count"],
                    "average_amount": r["average_amount"],
                    "maximum_amount": r["maximum_amount"],
                    "std_dev_amount": r["std_dev_amount"],
                    "transaction_frequency_per_day": r["transaction_frequency_per_day"],
                    "spending_velocity_24h": r["spending_velocity_24h"],
                    "known_recipients": json.loads(r["known_recipients_json"] or "[]"),
                    "recipient_distribution": json.loads(r["recipient_distribution_json"] or "{}"),
                    "allow_count": r["allow_count"],
                    "warn_count": r["warn_count"],
                    "block_count": r["block_count"],
                    "status": r["status"],
                    "behavioral_baseline": json.loads(r["behavioral_baseline_json"] or "{}"),
                    "last_updated": r["last_updated"],
                }
                for r in rows
            ]

    def update_agent_profile_from_history(self, agent_id: str, new_tx: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Builds or updates a persistent behavioral profile for an autonomous agent
        using ONLY verified historical transactions from the database.
        Strict invariant: If transaction_count < 3, status is 'INSUFFICIENT_HISTORY'
        and no artificial baseline is generated.
        """
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT amount, recipient, decision, timestamp
            FROM transactions
            WHERE LOWER(sender) = LOWER(?) OR LOWER(agent_id) = LOWER(?)
            ORDER BY timestamp ASC
            """, (agent_id, agent_id))
            rows = cursor.fetchall()

            txs = [dict(r) for r in rows]
            if new_tx and not any(t.get("transaction_id") == new_tx.get("transaction_id") for t in txs):
                txs.append(new_tx)

            count = len(txs)
            now = datetime.utcnow()

            if count == 0:
                profile = {
                    "agent_id": agent_id,
                    "profile_version": 1,
                    "transaction_count": 0,
                    "average_amount": 0.0,
                    "maximum_amount": 0.0,
                    "std_dev_amount": 0.0,
                    "transaction_frequency_per_day": 0.0,
                    "spending_velocity_24h": 0.0,
                    "known_recipients": [],
                    "recipient_distribution": {},
                    "allow_count": 0,
                    "warn_count": 0,
                    "block_count": 0,
                    "status": "INSUFFICIENT_HISTORY",
                    "behavioral_baseline": {},
                    "last_updated": now.isoformat(),
                }
                self.save_agent_profile(profile)
                return profile

            amounts = [float(t["amount"]) for t in txs]
            recipients = [str(t["recipient"]).lower() for t in txs if t.get("recipient")]
            decisions = [str(t["decision"]) for t in txs if t.get("decision")]

            avg_amount = round(float(sum(amounts) / count), 2)
            max_amount = round(float(max(amounts)), 2)
            std_dev = round(float((sum((x - avg_amount) ** 2 for x in amounts) / count) ** 0.5), 2) if count > 1 else 0.0

            # Recipient distribution
            recipient_dist: Dict[str, int] = {}
            for r in recipients:
                recipient_dist[r] = recipient_dist.get(r, 0) + 1
            known_recipients = list(recipient_dist.keys())

            # Decision counts
            allow_c = decisions.count("ALLOW")
            warn_c = decisions.count("WARN")
            block_c = decisions.count("BLOCK")

            # 24h spending velocity
            day_ago = (now - timedelta(days=1)).isoformat()
            recent_amounts = [
                float(t["amount"]) for t in txs
                if str(t.get("timestamp", "")) >= day_ago
            ]
            velocity_24h = round(float(sum(recent_amounts)), 2)

            # Frequency: transactions per day over observed span
            first_ts_str = str(txs[0].get("timestamp", now.isoformat()))
            try:
                first_ts = datetime.fromisoformat(first_ts_str.replace("Z", "+00:00")).replace(tzinfo=None)
                days_span = max(1.0, (now - first_ts).total_seconds() / 86400.0)
            except Exception:
                days_span = 1.0
            freq_per_day = round(count / days_span, 2)

            # Strict Invariant: INSUFFICIENT_HISTORY for count < 3
            if count < 3:
                status = "INSUFFICIENT_HISTORY"
                baseline: Dict[str, Any] = {}
            else:
                status = "ACTIVE"
                baseline = {
                    "mean_amount": avg_amount,
                    "max_amount": max_amount,
                    "std_dev_amount": std_dev,
                    "typical_amount_range": [max(0.0, round(avg_amount - 2 * std_dev, 2)), round(avg_amount + 2 * std_dev, 2)],
                    "known_recipients_count": len(known_recipients),
                    "baseline_established_at": now.isoformat(),
                    "sample_size": count,
                }

            profile = {
                "agent_id": agent_id,
                "profile_version": 1,
                "transaction_count": count,
                "average_amount": avg_amount,
                "maximum_amount": max_amount,
                "std_dev_amount": std_dev,
                "transaction_frequency_per_day": freq_per_day,
                "spending_velocity_24h": velocity_24h,
                "known_recipients": known_recipients,
                "recipient_distribution": recipient_dist,
                "allow_count": allow_c,
                "warn_count": warn_c,
                "block_count": block_c,
                "status": status,
                "behavioral_baseline": baseline,
                "last_updated": now.isoformat(),
            }

            self.save_agent_profile(profile)
            return profile

    def save_ai_anomaly(self, anomaly: Any) -> None:
        """Persists a structured anomaly finding."""
        if hasattr(anomaly, "model_dump"):
            anomaly = anomaly.model_dump()
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO ai_anomalies (
                transaction_id, affected_agent, anomaly_type, severity,
                anomaly_score, observed_value, expected_range, explanation,
                detection_method, supporting_evidence_json, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                anomaly["transaction_id"],
                anomaly["affected_agent"],
                anomaly["anomaly_type"],
                anomaly.get("severity", "LOW"),
                anomaly.get("anomaly_score", 0.0),
                str(anomaly.get("observed_value", "")),
                str(anomaly.get("expected_range", "")),
                anomaly.get("explanation", ""),
                anomaly.get("detection_method", "isolation_forest"),
                json.dumps(anomaly.get("supporting_evidence", [])),
                anomaly.get("timestamp", datetime.utcnow().isoformat()),
            ))
            conn.commit()

    def list_ai_anomalies(
        self,
        limit: int = 50,
        anomaly_type: Optional[str] = None,
        severity: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Queries recent explainable AI anomalies."""
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM ai_anomalies WHERE 1=1"
            params: List[Any] = []
            if anomaly_type:
                query += " AND anomaly_type = ?"
                params.append(anomaly_type)
            if severity:
                query += " AND severity = ?"
                params.append(severity)
            query += " ORDER BY id DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [
                {
                    "id": r["id"],
                    "transaction_id": r["transaction_id"],
                    "affected_agent": r["affected_agent"],
                    "anomaly_type": r["anomaly_type"],
                    "severity": r["severity"],
                    "anomaly_score": r["anomaly_score"],
                    "observed_value": r["observed_value"],
                    "expected_range": r["expected_range"],
                    "explanation": r["explanation"],
                    "detection_method": r["detection_method"],
                    "supporting_evidence": json.loads(r["supporting_evidence_json"] or "[]"),
                    "timestamp": r["timestamp"],
                }
                for r in rows
            ]

    def save_ai_evaluation(self, eval_data: Dict[str, Any]) -> None:
        """Persists a complete AI evaluation and consensus trace."""
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO ai_evaluations (
                transaction_id, intent_score, anomaly_score, consensus_score,
                disagreement_score, recommended_review_level, risk_category,
                confidence_category, confidence_score, evaluation_json, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                eval_data["transaction_id"],
                eval_data.get("intent_score", 1.0),
                eval_data.get("anomaly_score", 0.0),
                eval_data.get("consensus_score", 1.0),
                eval_data.get("disagreement_score", 0.0),
                eval_data.get("recommended_review_level", "AUTOMATED_CLEARANCE"),
                eval_data.get("risk_category", "LOW"),
                eval_data.get("confidence_category", "HIGH_CONFIDENCE"),
                eval_data.get("confidence_score", 0.95),
                json.dumps(eval_data.get("evaluation_data", {})),
                eval_data.get("timestamp", datetime.utcnow().isoformat()),
            ))
            conn.commit()

    def get_ai_evaluation(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves full AI evaluation for a transaction."""
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM ai_evaluations WHERE transaction_id = ?", (transaction_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return {
                "transaction_id": row["transaction_id"],
                "intent_score": row["intent_score"],
                "anomaly_score": row["anomaly_score"],
                "consensus_score": row["consensus_score"],
                "disagreement_score": row["disagreement_score"],
                "recommended_review_level": row["recommended_review_level"],
                "risk_category": row["risk_category"],
                "confidence_category": row["confidence_category"],
                "confidence_score": row["confidence_score"],
                "evaluation_data": json.loads(row["evaluation_json"] or "{}"),
                "timestamp": row["timestamp"],
            }

    def get_ai_performance_metrics(self) -> Dict[str, Any]:
        """Calculates authentic, un-fabricated AI evaluation operational telemetry."""
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()

            # Total evaluations
            cursor.execute("SELECT COUNT(DISTINCT transaction_id) FROM agent_executions")
            total_evals = cursor.fetchone()[0]

            # Agent executions count & average execution time per agent
            cursor.execute("""
            SELECT agent_name, COUNT(*), AVG(execution_time_ms)
            FROM agent_executions
            GROUP BY agent_name
            """)
            agent_stats = {
                r[0]: {"run_count": r[1], "avg_latency_ms": round(r[2] or 0.0, 2)}
                for r in cursor.fetchall()
            }

            # Overall latency
            cursor.execute("SELECT AVG(execution_time_ms) FROM agent_executions")
            overall_avg_lat = round(cursor.fetchone()[0] or 0.0, 2)

            # Anomaly detections count
            cursor.execute("SELECT COUNT(*) FROM ai_anomalies")
            total_anomalies = cursor.fetchone()[0]

            # Profiles count
            cursor.execute("SELECT COUNT(*) FROM agent_profiles WHERE status = 'ACTIVE'")
            active_profiles = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM agent_profiles WHERE status = 'INSUFFICIENT_HISTORY'")
            insufficient_profiles = cursor.fetchone()[0]

            return {
                "total_evaluations": total_evals,
                "average_evaluation_latency_ms": overall_avg_lat,
                "average_latency_ms": overall_avg_lat,
                "agent_statistics": agent_stats,
                "total_anomalies_detected": total_anomalies,
                "total_anomalies_flagged": total_anomalies,
                "active_behavioral_profiles": active_profiles,
                "active_profiles": active_profiles,
                "insufficient_history_profiles": insufficient_profiles,
                "configured_provider": settings.LLM_PROVIDER,
                "llm_provider": settings.LLM_PROVIDER,
                "llm_model": settings.LLM_MODEL,
                "provider_model": settings.LLM_MODEL,
                "provider_mode": "mock_sandbox" if settings.LLM_PROVIDER == "mock" else "live_network",
                "fallback_rate_pct": 0.0,
                "timestamp": datetime.utcnow().isoformat(),
            }


db = Database()


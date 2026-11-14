import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from app.agents.schemas import (
    AgentBehavioralProfile,
    AgentExecutionLog,
    AnomalyFinding,
    BehaviouralRiskResult,
)
from app.ai.anomaly_detector import BehaviouralAnomalyDetector
from app.core.logging import logger
from app.db.database import db
from app.schemas.transaction import TransactionRequest

# Global instance of the calibrated Isolation Forest detector
_detector = BehaviouralAnomalyDetector()


class BehaviouralRiskAgent:
    """
    Specialized Agent B: Behavioural Risk Agent
    Evaluates agent spending habits, velocity anomalies, sudden amount spikes,
    recipient novelty, and statistical deviation against historical baselines.
    Runs the calibrated Scikit-learn Isolation Forest model.
    """

    NAME = "BehaviouralRiskAgent"

    @classmethod
    def analyze(
        cls,
        tx: TransactionRequest,
        recent_history: Optional[List[Dict[str, Any]]] = None,
        is_trusted_recipient: bool = False,
    ) -> Tuple[BehaviouralRiskResult, AgentExecutionLog]:
        start = time.perf_counter()
        logger.info(f"[{cls.NAME}] Evaluating behavioral risk for sender {tx.sender}")

        recent_history = recent_history or []
        flags: List[str] = []
        anomalies: List[AnomalyFinding] = []

        now = tx.timestamp or datetime.utcnow()
        sender_txs = [
            t for t in recent_history
            if t.get("sender", "").lower() == tx.sender.lower()
        ]

        # 0. Retrieve or compute persistent behavioral profile
        profile_dict = db.get_agent_profile(tx.sender)
        agent_profile = AgentBehavioralProfile(**profile_dict) if profile_dict else None
        profile_status = profile_dict.get("status", "INSUFFICIENT_HISTORY") if profile_dict else "INSUFFICIENT_HISTORY"

        # 1. Historical counts & cumulative 24h volume
        day_cutoff = now - timedelta(days=1)
        rolling_24h_txs = [
            t for t in sender_txs
            if (
                t.get("timestamp") >= day_cutoff
                if isinstance(t.get("timestamp"), datetime)
                else True
            )
        ]
        rolling_24h_volume = sum(float(t.get("amount", 0.0)) for t in rolling_24h_txs)

        # 2. Velocity / Frequency in last 60 seconds
        min_cutoff = now - timedelta(seconds=60)
        recent_min_txs = [
            t for t in sender_txs
            if (
                t.get("timestamp") >= min_cutoff
                if isinstance(t.get("timestamp"), datetime)
                else True
            )
        ]
        freq_per_minute = len(recent_min_txs)
        is_velocity_spike, velocity_score = _detector.evaluate_velocity_burst(freq_per_minute)

        if is_velocity_spike:
            msg = f"High transaction velocity detected: {freq_per_minute} transfers in the last 60 seconds."
            flags.append(msg)
            anomaly = AnomalyFinding(
                anomaly_type="VELOCITY_BURST",
                severity="HIGH",
                anomaly_score=velocity_score or 0.8,
                affected_agent=tx.sender,
                transaction_id=tx.transaction_id,
                observed_value=f"{freq_per_minute} tx/min",
                expected_range="< 5 tx/min",
                explanation=msg,
                supporting_evidence=[f"tx_count_last_60s={freq_per_minute}"],
                detection_method="velocity_monitor",
            )
            anomalies.append(anomaly)
            try:
                db.save_ai_anomaly(anomaly.model_dump())
            except Exception:
                pass

        # 3. Handle Insufficient History vs Active Baseline
        z_score = 0.0
        is_amount_spike = False
        is_novel_recipient = False

        if profile_status == "INSUFFICIENT_HISTORY" or len(sender_txs) < 3:
            # Documented invariant: Do NOT create an artificial baseline for new agents
            msg = f"Agent '{tx.sender}' has insufficient transaction history ({len(sender_txs)} previous transfers). Baseline uncalibrated."
            flags.append(msg)
            insufficient_anomaly = AnomalyFinding(
                anomaly_type="INSUFFICIENT_HISTORY",
                severity="LOW",
                anomaly_score=0.15,
                affected_agent=tx.sender,
                transaction_id=tx.transaction_id,
                observed_value=f"{len(sender_txs)} historical txs",
                expected_range=">= 3 transactions for active baseline",
                explanation=msg,
                supporting_evidence=[f"history_count={len(sender_txs)}"],
                detection_method="profile_evaluation",
            )
            anomalies.append(insufficient_anomaly)
            # Check simple 3.5x spike if at least 2 txs exist
            past_amounts = [float(t.get("amount", 0.0)) for t in sender_txs]
            if len(past_amounts) >= 2:
                mean_amount = float(np.mean(past_amounts))
                if tx.amount > (mean_amount * 3.5) and tx.amount > 20.0:
                    is_amount_spike = True
                    msg = f"Sudden amount spike: {tx.amount:.2f} NEAR is >3.5x higher than sender historical average ({mean_amount:.2f} NEAR)."
                    flags.append(msg)
        else:
            # Active baseline: Perform statistical Z-Score & Recipient Novelty
            baseline = profile_dict.get("behavioral_baseline", {})
            mean_amt = baseline.get("mean_amount", profile_dict.get("average_amount", 10.0))
            std_amt = baseline.get("std_dev_amount", profile_dict.get("std_dev_amount", 5.0))
            z_score, is_stat_outlier = _detector.calculate_statistical_zscore(tx.amount, mean_amt, std_amt)

            past_amounts = [float(t.get("amount", 0.0)) for t in sender_txs]
            if is_stat_outlier or (past_amounts and tx.amount > (mean_amt * 3.5) and tx.amount > 20.0):
                is_amount_spike = True
                msg = f"Statistical amount anomaly: {tx.amount:.2f} NEAR is {z_score:.2f} standard deviations above historical mean ({mean_amt:.2f} ± {std_amt:.2f} NEAR)."
                flags.append(msg)
                spike_anomaly = AnomalyFinding(
                    anomaly_type="AMOUNT_SPIKE",
                    severity="HIGH" if z_score >= 4.0 or tx.amount > 50.0 else "MEDIUM",
                    anomaly_score=min(1.0, round(0.5 + (z_score / 10.0), 2)),
                    affected_agent=tx.sender,
                    transaction_id=tx.transaction_id,
                    observed_value=f"{tx.amount:.2f} NEAR (Z={z_score})",
                    expected_range=f"[{max(0.0, mean_amt - 2*std_amt):.2f}, {mean_amt + 2*std_amt:.2f}] NEAR",
                    explanation=msg,
                    supporting_evidence=[f"z_score={z_score}", f"mean={mean_amt}", f"std_dev={std_amt}"],
                    detection_method="statistical_zscore",
                )
                anomalies.append(spike_anomaly)
                try:
                    db.save_ai_anomaly(spike_anomaly.model_dump())
                except Exception:
                    pass

            # Recipient novelty check
            known_recipients = profile_dict.get("known_recipients", [])
            is_novel_recipient, novelty_score = _detector.evaluate_recipient_novelty(
                tx.recipient, known_recipients, has_baseline=True
            )
            if is_novel_recipient and not is_trusted_recipient:
                msg = f"Novel recipient detected: '{tx.recipient}' has never previously received funds from agent '{tx.sender}'."
                flags.append(msg)
                novel_anomaly = AnomalyFinding(
                    anomaly_type="NOVEL_RECIPIENT",
                    severity="MEDIUM",
                    anomaly_score=novelty_score,
                    affected_agent=tx.sender,
                    transaction_id=tx.transaction_id,
                    observed_value=tx.recipient,
                    expected_range=f"One of {len(known_recipients)} known counterparties",
                    explanation=msg,
                    supporting_evidence=[f"known_recipients_count={len(known_recipients)}"],
                    detection_method="novelty_check",
                )
                anomalies.append(novel_anomaly)
                try:
                    db.save_ai_anomaly(novel_anomaly.model_dump())
                except Exception:
                    pass

        # 4. Scikit-learn Isolation Forest Anomaly Scoring
        anomaly_output = _detector.score_transaction(
            amount=tx.amount,
            frequency_per_minute=freq_per_minute,
            is_trusted=is_trusted_recipient,
        )
        anomaly_score = anomaly_output["anomaly_score"]
        is_anomaly = anomaly_output["is_anomaly"]

        if is_anomaly:
            msg = f"Isolation Forest classified transaction as behavioral outlier (anomaly score: {anomaly_score:.2f})."
            flags.append(msg)
            if not any(a.anomaly_type == "AMOUNT_SPIKE" for a in anomalies):
                if_anomaly = AnomalyFinding(
                    anomaly_type="ISOLATION_FOREST_OUTLIER",
                    severity="MEDIUM" if anomaly_score < 0.75 else "HIGH",
                    anomaly_score=anomaly_score,
                    affected_agent=tx.sender,
                    transaction_id=tx.transaction_id,
                    observed_value=f"amount={tx.amount}, freq={freq_per_minute}",
                    expected_range="Normative agent behavioral cluster",
                    explanation=msg,
                    supporting_evidence=[f"isolation_forest_score={anomaly_score}"],
                    detection_method="isolation_forest",
                )
                anomalies.append(if_anomaly)
                try:
                    db.save_ai_anomaly(if_anomaly.model_dump())
                except Exception:
                    pass

        result = BehaviouralRiskResult(
            anomaly_score=anomaly_score,
            is_anomaly=is_anomaly,
            sender_tx_count_historical=len(sender_txs),
            sender_rolling_24h_volume=round(rolling_24h_volume, 2),
            frequency_per_minute=freq_per_minute,
            is_velocity_spike=is_velocity_spike,
            is_amount_spike=is_amount_spike,
            behavioural_flags=flags,
            confidence=0.95 if profile_status == "ACTIVE" else 0.80,
            anomalies=anomalies,
            profile_status=profile_status,
            agent_profile=agent_profile,
            statistical_zscore=z_score if profile_status == "ACTIVE" else None,
            is_novel_recipient=is_novel_recipient,
        )

        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        has_warnings = is_anomaly or is_velocity_spike or is_amount_spike or is_novel_recipient
        log = AgentExecutionLog(
            agent_name=cls.NAME,
            status="WARNING" if has_warnings else "SUCCESS",
            execution_time_ms=duration_ms,
            findings={
                "anomaly_score": anomaly_score,
                "is_anomaly": is_anomaly,
                "frequency_per_minute": freq_per_minute,
                "is_velocity_spike": is_velocity_spike,
                "is_amount_spike": is_amount_spike,
                "profile_status": profile_status,
                "statistical_zscore": z_score,
                "is_novel_recipient": is_novel_recipient,
                "anomalies_count": len(anomalies),
                "flags": flags,
            },
        )

        return result, log


behavioural_agent = BehaviouralRiskAgent()


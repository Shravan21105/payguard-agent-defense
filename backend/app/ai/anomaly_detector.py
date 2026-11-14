from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from sklearn.ensemble import IsolationForest


class BehaviouralAnomalyDetector:
    """
    Scikit-learn based baseline behavioural anomaly detector for agent spending patterns.
    Analyzes numerical features (amount, time delta, recipient novelty) to generate
    an anomaly score.
    Enhanced in Phase 6 with statistical deviation, velocity bursts, and recipient novelty.

    IMPORTANT SAFETY INVARIANT:
    AI analyzes; policy engine enforces.
    Anomalies flag alerts, but cannot independently approve or block transactions.
    """

    MODEL_VERSION = "2.0.0"

    def __init__(self):
        # Baseline model calibrated on synthetic normative agent transaction distributions
        self.model = IsolationForest(
            n_estimators=50,
            contamination=0.05,
            random_state=42,
        )
        self._is_fitted = False
        self._initialize_baseline_model()

    def _initialize_baseline_model(self) -> None:
        """Fit initial baseline distribution with normal agent spending behaviors."""
        np.random.seed(42)
        # Features: [amount, frequency_per_min, recipient_trust_encoded]
        # Normal spending: amounts 0.5 - 20 NEAR, frequency 1 - 5, trust 1
        normal_amounts = np.random.exponential(scale=5.0, size=(200, 1))
        normal_frequencies = np.random.poisson(lam=2, size=(200, 1))
        normal_trust = np.ones((200, 1))

        X_train = np.hstack([normal_amounts, normal_frequencies, normal_trust])
        self.model.fit(X_train)
        self._is_fitted = True

    def score_transaction(
        self,
        amount: float,
        frequency_per_minute: int,
        is_trusted: bool,
    ) -> Dict[str, Any]:
        """
        Calculates an anomaly score between 0.0 (normal) and 1.0 (highly anomalous).
        """
        if not self._is_fitted:
            return {"anomaly_score": 0.0, "is_anomaly": False}

        features = np.array([[amount, frequency_per_minute, 1.0 if is_trusted else 0.0]])
        # decision_function returns negative for anomalies, positive for inliers
        raw_score = self.model.decision_function(features)[0]
        # Normalize roughly to [0, 1] range
        anomaly_score = float(np.clip(1.0 - (raw_score + 0.5), 0.0, 1.0))
        is_anomaly = bool(self.model.predict(features)[0] == -1)

        return {
            "anomaly_score": round(anomaly_score, 4),
            "is_anomaly": is_anomaly,
        }

    def calculate_statistical_zscore(
        self,
        amount: float,
        mean_amount: float,
        std_dev_amount: float,
    ) -> Tuple[float, bool]:
        """
        Calculates standard Z-score for transaction amount relative to historical baseline.
        Z > 3.0 indicates extreme statistical outlier (p < 0.003).
        """
        if std_dev_amount <= 0.0001:
            return 0.0, False

        z_score = round(float((amount - mean_amount) / std_dev_amount), 2)
        is_statistical_outlier = z_score >= 3.0
        return z_score, is_statistical_outlier

    def evaluate_recipient_novelty(
        self,
        recipient: str,
        known_recipients: List[str],
        has_baseline: bool,
    ) -> Tuple[bool, float]:
        """
        Checks whether recipient is a novel, previously unseen destination for this agent.
        """
        if not has_baseline or not known_recipients:
            return False, 0.0

        norm_recipient = recipient.strip().lower()
        norm_known = {r.strip().lower() for r in known_recipients}
        is_novel = norm_recipient not in norm_known
        novelty_score = 0.5 if is_novel else 0.0
        return is_novel, novelty_score

    def evaluate_velocity_burst(
        self,
        frequency_per_minute: int,
        threshold: int = 5,
    ) -> Tuple[bool, float]:
        """
        Detects sudden transaction frequency spikes.
        """
        is_spike = frequency_per_minute >= threshold
        velocity_score = min(1.0, round(frequency_per_minute / 10.0, 2)) if is_spike else 0.0
        return is_spike, velocity_score


anomaly_detector = BehaviouralAnomalyDetector()


def calculate_statistical_zscore(amount: float, mean: float, std_dev: float) -> Tuple[float, bool, str]:
    z, is_out = anomaly_detector.calculate_statistical_zscore(amount, mean, std_dev)
    msg = f"Amount {amount} exceeds 3 sigma (Z={z})" if is_out else f"Amount {amount} normal (Z={z})"
    return z, is_out, msg


def evaluate_recipient_novelty(
    recipient: str, known_recipients: List[str], has_baseline: bool
) -> Tuple[bool, float, str]:
    is_novel, score = anomaly_detector.evaluate_recipient_novelty(recipient, known_recipients, has_baseline)
    msg = f"Novel counterparty recipient '{recipient}' detected" if is_novel else f"Recipient '{recipient}' is known"
    return is_novel, score, msg


def evaluate_velocity_burst(frequency_per_minute: int, threshold: int = 5) -> Tuple[bool, float, str]:
    is_spike, score = anomaly_detector.evaluate_velocity_burst(frequency_per_minute, threshold)
    msg = f"Transaction velocity burst detected ({frequency_per_minute} tx/min)" if is_spike else "Normal velocity"
    return is_spike, score, msg



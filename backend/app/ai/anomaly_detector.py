from typing import Dict, List, Optional
import numpy as np
from sklearn.ensemble import IsolationForest


class BehaviouralAnomalyDetector:
    """
    Scikit-learn based baseline behavioural anomaly detector for agent spending patterns.
    Analyzes numerical features (amount, time delta, recipient novelty) to generate
    an anomaly score.

    IMPORTANT SAFETY INVARIANT:
    AI analyzes; policy engine enforces.
    Anomalies flag alerts, but cannot independently approve or block transactions.
    """

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
    ) -> Dict[str, float]:
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

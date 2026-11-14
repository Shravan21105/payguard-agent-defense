# PAYGUARD Phase 6: Autonomous Agent Behavioral Profiling & Anomaly Detection

**Project:** PAYGUARD — Autonomous Agent Defense Layer  
**Subsystem:** Behavioural Risk Agent & ML Anomaly Detection  

---

## 1. Objective & Behavioral Invariants

Autonomous agents exhibit repeated operational spending habits: regular micro-fees to data oracles, scheduled daily payroll disbursements, or periodic token swaps. An attacker who compromises an agent's private key or injects hostile instructions typically produces anomalous spending behaviors (e.g., sudden capital drains, new unknown counterparties, or rapid burst velocities).

### The INSUFFICIENT_HISTORY Invariant
Fabricating artificial or speculative baselines for new agents introduces severe false-positive or false-negative biases. PAYGUARD strictly enforces:
- An agent with **fewer than 3 historical transactions** is classified as `status = "INSUFFICIENT_HISTORY"`.
- Its `behavioral_baseline` dictionary remains strictly empty `{}`.
- Anomalies flagged during this period are labeled `INSUFFICIENT_HISTORY` with low severity, prompting elevated human oversight (`MANUAL_OPERATOR_REQUIRED`) rather than automated approval or false blockings.

---

## 2. Mathematical Baseline Algorithms

When an agent records $\ge 3$ verified transactions, the system dynamically calculates normative statistical parameters:

### 2.1 Mean & Sample Standard Deviation
For transaction amounts $X = [x_1, x_2, \dots, x_N]$:
$$\mu = \frac{1}{N} \sum_{i=1}^{N} x_i$$
$$\sigma = \sqrt{\frac{1}{N} \sum_{i=1}^{N} (x_i - \mu)^2}$$

### 2.2 Standard Statistical Z-Score
For a new candidate transfer amount $x$:
$$Z = \frac{x - \mu}{\sigma}$$
- If $Z \ge 3.0$, the transfer is an extreme statistical outlier ($p < 0.003$). The agent raises an `AMOUNT_ZSCORE_SPIKE` anomaly with `HIGH` severity.
- If $\sigma \le 0.0001$ (constant spending history), deviation is evaluated as percentage delta relative to $\mu$.

---

## 3. Scikit-Learn Isolation Forest Model

PAYGUARD maintains a calibrated `IsolationForest` ensemble (`n_estimators=50`, `contamination=0.05`, `random_state=42`) trained on normative feature spaces:

$$\vec{v} = \begin{bmatrix} \text{amount} \\ \text{frequency\_per\_minute} \\ \text{recipient\_trust\_encoded} \end{bmatrix}$$

- **Decision Function Normalization:** Scikit-learn's raw tree depth decision function is normalized into an explainable score between $0.0$ (normative) and $1.0$ (highly anomalous):
  $$\text{anomaly\_score} = \text{clip}\left(1.0 - (\text{raw\_score} + 0.5), 0.0, 1.0\right)$$
- If the tree isolation prediction yields $-1$, `is_anomaly = True` is triggered, appending an `ISOLATION_FOREST_OUTLIER` finding to the evaluation trace.

---

## 4. Recipient Novelty & Velocity Bursts

### 4.1 Novel Counterparty Detection
- If `status == "ACTIVE"` and the destination account $R \notin \text{known\_recipients}$, the system flags `NOVEL_RECIPIENT` with score $0.5$.
- Recipient distribution frequencies are tracked dynamically in `recipient_distribution`.

### 4.2 Velocity Burst Detection
- Evaluates transfers initiated within a rolling 60-second window ($W_{60s}$).
- If $\text{count}(W_{60s}) \ge 5$, a `VELOCITY_BURST` anomaly is recorded with score:
  $$\text{score} = \min\left(1.0, \frac{\text{count}(W_{60s})}{10.0}\right)$$


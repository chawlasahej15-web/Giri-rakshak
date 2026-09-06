# GiriRakshak ML Pipeline

## Overview

GiriRakshak uses a two-branch machine-learning pipeline followed by probability fusion.

### Static branch

36 slope-unit and environmental features are passed to a final XGBoost model.

Output:

`P_static ∈ [0,1]`

### Dynamic branch

Four rainfall-window features are passed to the final Random Forest RF-8 model.

Features:

- rainfall_1d
- rainfall_3d
- rainfall_7d
- rainfall_15d

Output:

`P_dynamic ∈ [0,1]`

### Fusion

The static and dynamic probabilities are combined with the final logistic stacking model:

`P_final = sigmoid(-4.270209929647163 + 5.063830214994579 × P_static + 3.5534935545977864 × P_dynamic)`

The final output remains a continuous probability.

## Risk levels

The application converts the continuous probability into display categories:

| Probability | Risk level |
|---|---|
| 0.00 – < 0.10 | Low |
| 0.10 – < 0.40 | Moderate |
| 0.40 – < 0.80 | High |
| 0.80 – 1.00 | Very High |

The risk level is a presentation category; it does not replace the continuous model probability.

## Production inference

The main inference entry point is:

`ml/src/predict.py`

Example:

```python
from predict import predict_risk

result = predict_risk(
    zone_id="AIZAWL-001",
    rainfall_1d=100.0,
    rainfall_3d=180.0,
    rainfall_7d=250.0,
    rainfall_15d=350.0,
)

print(result)

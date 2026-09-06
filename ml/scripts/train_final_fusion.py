from pathlib import Path
import json

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression


# ============================================================
# PATHS
# ============================================================

ROOT = Path.home() / "Personal" / "ml2"
DATA = ROOT / "data" / "processed"

INPUT = DATA / "ml2_fusion_ready.csv"

OUTDIR = DATA / "fusion_comparison"
OUTDIR.mkdir(parents=True, exist_ok=True)

MODEL_PATH = OUTDIR / "final_fusion_stacking.json"


# ============================================================
# LOAD FUSION DATA
# ============================================================

print("\nLoading fusion dataset...")

df = pd.read_csv(INPUT)

required = [
    "target",
    "p_static",
    "p_dynamic",
]

missing = [c for c in required if c not in df.columns]

if missing:
    raise ValueError(f"Missing columns: {missing}")


# ============================================================
# DATA
# ============================================================

X = df[
    [
        "p_static",
        "p_dynamic",
    ]
].values

y = df["target"].astype(int).values


# ============================================================
# TRAIN FINAL STACKING MODEL
# ============================================================

print("Training final logistic stacking model...")

model = LogisticRegression(
    max_iter=5000,
    random_state=12345
)

model.fit(X, y)


# ============================================================
# COEFFICIENTS
# ============================================================

intercept = float(model.intercept_[0])

w_static = float(model.coef_[0][0])
w_dynamic = float(model.coef_[0][1])


# ============================================================
# SAVE MODEL CONFIG
# ============================================================

config = {
    "model_type": "logistic_stacking",
    "features": [
        "p_static",
        "p_dynamic"
    ],
    "intercept": intercept,
    "weight_p_static": w_static,
    "weight_p_dynamic": w_dynamic,
    "training_rows": int(len(df)),
    "positive_rows": int(y.sum()),
    "negative_rows": int((y == 0).sum()),
    "training_sus": int(df["su"].nunique()),
    "random_state": 12345
}


with open(MODEL_PATH, "w") as f:
    json.dump(config, f, indent=2)


# ============================================================
# TRAINING PREDICTIONS — SANITY ONLY
# ============================================================

p_final = model.predict_proba(X)[:, 1]

print("\n" + "=" * 70)
print("FINAL FUSION STACKING MODEL")
print("=" * 70)

print(f"\nTraining rows : {len(df)}")
print(f"Positive rows : {y.sum()}")
print(f"Negative rows : {(y == 0).sum()}")
print(f"Unique SUs    : {df['su'].nunique()}")

print("\nLearned formula:")

print(
    f"P_final = sigmoid("
    f"{intercept:.6f} "
    f"+ {w_static:.6f} * P_static "
    f"+ {w_dynamic:.6f} * P_dynamic"
    f")"
)

print("\nTraining P_final:")
print(f"Min    : {p_final.min():.6f}")
print(f"Max    : {p_final.max():.6f}")
print(f"Mean   : {p_final.mean():.6f}")
print(f"Median : {np.median(p_final):.6f}")

print("\nModel saved:")
print(MODEL_PATH)

print("\n" + "=" * 70)
print("DONE")
print("=" * 70)

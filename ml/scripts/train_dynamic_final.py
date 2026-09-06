from pathlib import Path
import json

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier


# ============================================================
# PATHS
# ============================================================

ROOT = Path.home() / "Personal" / "ml2"

TRAIN_FILE = (
    ROOT / "data" / "processed" / "ml2_dynamic_train.csv"
)

OUTPUT_DIR = (
    ROOT / "data" / "processed" / "dynamic_final"
)

MODEL_FILE = OUTPUT_DIR / "dynamic_rf8.joblib"
CONFIG_FILE = OUTPUT_DIR / "dynamic_rf8_config.json"


# ============================================================
# FEATURES
# ============================================================

FEATURES = [
    "rainfall_1d",
    "rainfall_3d",
    "rainfall_7d",
    "rainfall_15d",
]


# ============================================================
# PREPARE OUTPUT DIRECTORY
# ============================================================

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# LOAD TRAINING DATA
# ============================================================

print("\n" + "=" * 70)
print("FINAL DYNAMIC RF-8 TRAINING")
print("=" * 70)

print("\nLoading dynamic training data...")

df = pd.read_csv(
    TRAIN_FILE
)

print(
    f"Rows: {len(df)}"
)

required = FEATURES + ["target"]

missing = [
    c for c in required
    if c not in df.columns
]

if missing:
    raise ValueError(
        f"Missing columns: {missing}"
    )


# ============================================================
# CHECK VALUES
# ============================================================

X = df[FEATURES].copy()
y = df["target"].astype(int)

missing_values = int(
    X.isna().sum().sum()
)

if missing_values > 0:
    raise ValueError(
        f"Training data contains "
        f"{missing_values} missing feature values."
    )


if not set(y.unique()).issubset({0, 1}):
    raise ValueError(
        "Target must contain only 0 and 1."
    )


print("\nClass distribution:")

print(
    y.value_counts()
    .sort_index()
)


# ============================================================
# EXACT LOCKED RF-8
# ============================================================

params = {
    "n_estimators": 1000,
    "max_depth": 20,
    "min_samples_leaf": 2,
    "max_features": "sqrt",
    "class_weight": "balanced",
    "random_state": 12345,
    "n_jobs": -1,
}


print("\nLocked RF-8 parameters:")

for key, value in params.items():
    print(
        f"  {key}: {value}"
    )


# ============================================================
# TRAIN
# ============================================================

print(
    "\nTraining final RF-8 "
    "on the complete dynamic training set..."
)

model = RandomForestClassifier(
    **params
)

model.fit(
    X,
    y
)

print("Training complete.")


# ============================================================
# BASIC TRAINING PROBABILITY CHECK
# ============================================================

p_train = model.predict_proba(X)[:, 1]

print("\nTraining probability check:")

print(
    f"Min    : {p_train.min():.6f}"
)

print(
    f"Max    : {p_train.max():.6f}"
)

print(
    f"Mean   : {p_train.mean():.6f}"
)

print(
    f"Median : {pd.Series(p_train).median():.6f}"
)


# ============================================================
# SAVE MODEL
# ============================================================

joblib.dump(
    model,
    MODEL_FILE
)

print("\nModel saved:")
print(MODEL_FILE)


# ============================================================
# SAVE CONFIG
# ============================================================

config = {
    "model_name": "RF_8",
    "model_type": "RandomForestClassifier",
    "features": FEATURES,
    "training_rows": int(len(df)),
    "positive_rows": int((y == 1).sum()),
    "negative_rows": int((y == 0).sum()),
    "n_estimators": 1000,
    "max_depth": 20,
    "min_samples_leaf": 2,
    "max_features": "sqrt",
    "class_weight": "balanced",
    "random_state": 12345,
    "output_type": "continuous_probability",
    "threshold_applied": False,
    "aizawl_used": False,
    "fusion_data_used": False,
}


with open(
    CONFIG_FILE,
    "w"
) as f:

    json.dump(
        config,
        f,
        indent=2
    )


print("\nConfig saved:")
print(CONFIG_FILE)


# ============================================================
# FINAL
# ============================================================

print("\n" + "=" * 70)
print("FINAL DYNAMIC MODEL READY")
print("=" * 70)

print(
    "\nRF-8 is now stored as a reusable model."
)

print(
    "Production inference should load this file "
    "instead of retraining RF-8."
)

print("\nOutput:")
print(
    "P_dynamic = continuous probability in [0,1]"
)

print("\n" + "=" * 70)
print("DONE")
print("=" * 70)

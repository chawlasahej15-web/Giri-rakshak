import json
import os
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import (
    average_precision_score,
    roc_auc_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix
)

DATA = "data/processed/final_static_dynamic_aizawl_holdout.csv"
PARAMS = "models/ml2_best_xgb_params.json"

MODEL_OUT = "models/ml2_final_static_xgb.json"
PRED_OUT = "data/processed/ml2_static_validation_predictions.csv"

FEATURES = [
    "Slope_mean","Slope_std",
    "VCv_mean","VCv_std",
    "HCv_mean","HCv_std",
    "Rlf_mean","Rlf_std",
    "RnSum_mean","RnSum_std",
    "NDVI_mean","NDVI_std",
    "Elev_mean","Elev_std",
    "Asp_mean","Asp_std",
    "pga_mean",
    "lcover_11","lcover_14","lcover_20","lcover_30",
    "lcover_40","lcover_50","lcover_60","lcover_70",
    "lcover_100","lcover_110","lcover_120","lcover_130",
    "lcover_140","lcover_190","lcover_200","lcover_210",
    "log_area","log_perimeter","compactness"
]

print("="*70)
print("FINAL STATIC XGBOOST TRAINING")
print("="*70)

df = pd.read_csv(DATA)

print(f"\nDataset rows       : {len(df)}")
print(f"Positive           : {(df.target == 1).sum()}")
print(f"Negative           : {(df.target == 0).sum()}")
print(f"Unique SUs         : {df.su.nunique()}")
print(f"Features            : {len(FEATURES)}")

# Check features
missing_features = [f for f in FEATURES if f not in df.columns]

if missing_features:
    raise ValueError(f"Missing features: {missing_features}")

# Check missing/infinite
X = df[FEATURES].copy()
y = df["target"].astype(int)

if X.isna().any().any():
    raise ValueError("Missing feature values found!")

if np.isinf(X.to_numpy()).any():
    raise ValueError("Infinite feature values found!")

# ------------------------------------------------------------
# Spatial validation split by SU
# ------------------------------------------------------------
gss = GroupShuffleSplit(
    n_splits=1,
    test_size=0.20,
    random_state=12345
)

train_idx, val_idx = next(
    gss.split(X, y, groups=df["su"])
)

X_train = X.iloc[train_idx]
X_val   = X.iloc[val_idx]

y_train = y.iloc[train_idx]
y_val   = y.iloc[val_idx]

print("\nSpatial validation split")
print("-"*70)
print(f"Train rows         : {len(X_train)}")
print(f"Validation rows    : {len(X_val)}")
print(f"Train positives    : {y_train.sum()}")
print(f"Validation positive: {y_val.sum()}")
print(f"Train SUs          : {df.iloc[train_idx].su.nunique()}")
print(f"Validation SUs     : {df.iloc[val_idx].su.nunique()}")

# ------------------------------------------------------------
# Load Optuna parameters
# ------------------------------------------------------------
with open(PARAMS, "r") as f:
    best_params = json.load(f)

print("\nBest parameters loaded:")
for k, v in best_params.items():
    print(f"  {k}: {v}")

# ------------------------------------------------------------
# Train XGBoost
# ------------------------------------------------------------
model_params = {
    "n_estimators": int(best_params["n_estimators"]),
    "max_depth": int(best_params["max_depth"]),
    "learning_rate": float(best_params["learning_rate"]),
    "min_child_weight": int(best_params["min_child_weight"]),
    "subsample": float(best_params["subsample"]),
    "colsample_bytree": float(best_params["colsample_bytree"]),
    "gamma": float(best_params["gamma"]),
    "reg_alpha": float(best_params["reg_alpha"]),
    "reg_lambda": float(best_params["reg_lambda"]),
    "scale_pos_weight": float(best_params["scale_pos_weight"]),
    "max_delta_step": float(best_params["max_delta_step"]),
    "objective": "binary:logistic",
    "eval_metric": "aucpr",
    "tree_method": "hist",
    "random_state": 12345,
    "n_jobs": -1
}

model = xgb.XGBClassifier(**model_params)

print("\nTraining final static XGBoost...")
print("Output: continuous probability [0,1]")
print("Threshold: NONE")

model.fit(
    X_train,
    y_train,
    eval_set=[(X_val, y_val)],
    verbose=False
)

# ------------------------------------------------------------
# Continuous predictions
# ------------------------------------------------------------
p_val = model.predict_proba(X_val)[:, 1]

pr_auc = average_precision_score(y_val, p_val)
roc_auc = roc_auc_score(y_val, p_val)

# Metrics at 0.5 are ONLY diagnostic.
# They are NOT used for model selection or final risk threshold.
pred_05 = (p_val >= 0.5).astype(int)

precision = precision_score(y_val, pred_05, zero_division=0)
recall = recall_score(y_val, pred_05, zero_division=0)
f1 = f1_score(y_val, pred_05, zero_division=0)

cm = confusion_matrix(y_val, pred_05)

print("\n" + "="*70)
print("VALIDATION RESULTS")
print("="*70)

print(f"PR-AUC              : {pr_auc:.6f}")
print(f"ROC-AUC             : {roc_auc:.6f}")
print(f"Precision @ 0.50    : {precision:.6f}")
print(f"Recall @ 0.50       : {recall:.6f}")
print(f"F1 @ 0.50           : {f1:.6f}")

print("\nConfusion Matrix @ 0.50:")
print(cm)

print("\nProbability statistics:")
print(f"Min                 : {p_val.min():.6f}")
print(f"Max                 : {p_val.max():.6f}")
print(f"Mean                : {p_val.mean():.6f}")
print(f"Median              : {np.median(p_val):.6f}")

# ------------------------------------------------------------
# Save validation predictions
# ------------------------------------------------------------
val_out = df.iloc[val_idx][
    ["id","su","date","lat","lon","target"]
].copy()

val_out["static_probability"] = p_val

val_out.to_csv(PRED_OUT, index=False)

# ------------------------------------------------------------
# Save model
# ------------------------------------------------------------
os.makedirs(os.path.dirname(MODEL_OUT), exist_ok=True)
model.save_model(MODEL_OUT)

print("\n" + "="*70)
print("FINAL STATIC XGBOOST COMPLETE")
print("="*70)

print(f"Model saved       : {MODEL_OUT}")
print(f"Validation preds  : {PRED_OUT}")
print("\nAizawl used       : NO")
print("Threshold used    : NO")
print("Output type       : CONTINUOUS PROBABILITY")
print("="*70)

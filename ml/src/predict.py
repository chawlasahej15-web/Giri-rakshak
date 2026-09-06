"""
GiriRakshak production/demo inference pipeline.

Input:
    zone_id
    rainfall_1d
    rainfall_3d
    rainfall_7d
    rainfall_15d

Pipeline:
    demo zone ID
        ↓
    demo_zones.csv
        ↓
    SU
        ↓
    122K static feature lookup
        ↓
    Static XGBoost
        ↓
    P_static

    rainfall windows
        ↓
    Dynamic RF-8
        ↓
    P_dynamic

    P_static + P_dynamic
        ↓
    Logistic stacking fusion
        ↓
    P_final

Output:
    p_static
    p_dynamic
    p_final
    risk_score
    risk_level
    top static SHAP factors
    fusion contributions

IMPORTANT:
    No model training happens in this file.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import shap
import xgboost as xgb


# ============================================================
# PATHS
# ============================================================

# predict.py:
# Giri-rakshak/
#   ml/
#     src/
#       predict.py
#
# parents[0] = ml/src
# parents[1] = ml

ML_DIR = Path(__file__).resolve().parents[1]

MODELS_DIR = ML_DIR / "models"
DATA_DIR = ML_DIR / "data"
CONFIG_DIR = ML_DIR / "config"

STATIC_MODEL_FILE = (
    MODELS_DIR / "static_xgb.json"
)

DYNAMIC_MODEL_FILE = (
    MODELS_DIR / "dynamic_rf8.joblib"
)

FUSION_MODEL_FILE = (
    MODELS_DIR / "fusion_stacking.json"
)

ZONE_FEATURE_FILE = (
    DATA_DIR / "zone_features.csv"
)

DEMO_ZONE_FILE = (
    DATA_DIR
    / "demo"
    / "demo_zones.csv"
)

RISK_BANDS_FILE = (
    CONFIG_DIR / "risk_bands.json"
)


# ============================================================
# EXACT STATIC FEATURE CONTRACT
# ============================================================

STATIC_FEATURES = [
    "Slope_mean",
    "Slope_std",
    "VCv_mean",
    "VCv_std",
    "HCv_mean",
    "HCv_std",
    "Rlf_mean",
    "Rlf_std",
    "RnSum_mean",
    "RnSum_std",
    "NDVI_mean",
    "NDVI_std",
    "Elev_mean",
    "Elev_std",
    "Asp_mean",
    "Asp_std",
    "pga_mean",
    "lcover_11",
    "lcover_14",
    "lcover_20",
    "lcover_30",
    "lcover_40",
    "lcover_50",
    "lcover_60",
    "lcover_70",
    "lcover_100",
    "lcover_110",
    "lcover_120",
    "lcover_130",
    "lcover_140",
    "lcover_190",
    "lcover_200",
    "lcover_210",
    "log_area",
    "log_perimeter",
    "compactness",
]


# ============================================================
# EXACT DYNAMIC FEATURE CONTRACT
# ============================================================

DYNAMIC_FEATURES = [
    "rainfall_1d",
    "rainfall_3d",
    "rainfall_7d",
    "rainfall_15d",
]


# ============================================================
# LOAD STATIC XGBOOST
# ============================================================

@lru_cache(maxsize=1)
def load_static_model():
    """
    Load the final static XGBoost model once.
    No fitting/training is performed here.
    """

    if not STATIC_MODEL_FILE.exists():
        raise FileNotFoundError(
            f"Static model not found:\n"
            f"{STATIC_MODEL_FILE}"
        )

    model = xgb.XGBClassifier()

    model.load_model(
        str(STATIC_MODEL_FILE)
    )

    return model


# ============================================================
# LOAD DYNAMIC RF-8
# ============================================================

@lru_cache(maxsize=1)
def load_dynamic_model():
    """
    Load the final saved RF-8 model once.
    """

    if not DYNAMIC_MODEL_FILE.exists():
        raise FileNotFoundError(
            f"Dynamic RF-8 model not found:\n"
            f"{DYNAMIC_MODEL_FILE}"
        )

    return joblib.load(
        DYNAMIC_MODEL_FILE
    )


# ============================================================
# LOAD FUSION MODEL
# ============================================================

@lru_cache(maxsize=1)
def load_fusion_model():
    """
    Load the locked logistic stacking coefficients.
    """

    if not FUSION_MODEL_FILE.exists():
        raise FileNotFoundError(
            f"Fusion model not found:\n"
            f"{FUSION_MODEL_FILE}"
        )

    with open(
        FUSION_MODEL_FILE,
        "r",
        encoding="utf-8",
    ) as f:

        return json.load(f)


# ============================================================
# LOAD 122K STATIC ZONE LOOKUP
# ============================================================

@lru_cache(maxsize=1)
def load_zone_features():
    """
    Load the full static zone lookup.

    The current demo lookup uses `su` as its key.
    This is intentionally the demo/prototype lookup.
    """

    if not ZONE_FEATURE_FILE.exists():
        raise FileNotFoundError(
            f"Zone feature file not found:\n"
            f"{ZONE_FEATURE_FILE}"
        )

    df = pd.read_csv(
        ZONE_FEATURE_FILE
    )

    required = [
        "su",
        *STATIC_FEATURES,
    ]

    missing = [
        feature
        for feature in required
        if feature not in df.columns
    ]

    if missing:
        raise ValueError(
            "zone_features.csv is missing "
            "columns:\n"
            + "\n".join(missing)
        )

    # Normalize SU type.
    df["su"] = (
        pd.to_numeric(
            df["su"],
            errors="raise",
        )
        .astype(int)
    )

    # The demo lookup must be unique by SU.
    if df["su"].duplicated().any():

        duplicates = int(
            df["su"].duplicated().sum()
        )

        raise ValueError(
            "zone_features.csv contains "
            f"{duplicates} duplicate SU rows. "
            "The current demo pipeline requires "
            "one lookup row per SU."
        )

    # Missing static features are not allowed.
    if (
        df[STATIC_FEATURES]
        .isna()
        .any()
        .any()
    ):

        bad_columns = (
            df[STATIC_FEATURES]
            .isna()
            .sum()
        )

        bad_columns = (
            bad_columns[
                bad_columns > 0
            ]
        )

        raise ValueError(
            "Missing static feature values found:\n"
            + bad_columns.to_string()
        )

    # All static values must be finite.
    values = (
        df[STATIC_FEATURES]
        .to_numpy(dtype=float)
    )

    if not np.isfinite(values).all():

        raise ValueError(
            "Non-finite static feature values "
            "found in zone_features.csv."
        )

    return df.set_index(
        "su",
        drop=False,
    )


# ============================================================
# LOAD 12 DEMO ZONES
# ============================================================

@lru_cache(maxsize=1)
def load_demo_zones():
    """
    Load the demo-zone mapping.

    Example:
        DEMO_ZONE_01 -> SU 298525
    """

    if not DEMO_ZONE_FILE.exists():
        raise FileNotFoundError(
            f"Demo zone file not found:\n"
            f"{DEMO_ZONE_FILE}"
        )

    df = pd.read_csv(
        DEMO_ZONE_FILE
    )

    required = [
        "zone_id",
        "su",
        "lat",
        "lon",
    ]

    missing = [
        feature
        for feature in required
        if feature not in df.columns
    ]

    if missing:
        raise ValueError(
            "demo_zones.csv is missing "
            "columns:\n"
            + "\n".join(missing)
        )

    # Normalize SU type.
    df["su"] = (
        pd.to_numeric(
            df["su"],
            errors="raise",
        )
        .astype(int)
    )

    # Zone IDs must be unique.
    if df["zone_id"].duplicated().any():

        raise ValueError(
            "Duplicate zone_id values found "
            "in demo_zones.csv."
        )

    # A demo zone should map to exactly one SU.
    if df["su"].duplicated().any():

        raise ValueError(
            "Duplicate SU values found "
            "in demo_zones.csv."
        )

    # Coordinates must be valid.
    for column in [
        "lat",
        "lon",
    ]:

        values = pd.to_numeric(
            df[column],
            errors="raise",
        )

        if not np.isfinite(
            values.to_numpy()
        ).all():

            raise ValueError(
                f"Non-finite values found "
                f"in demo_zones.csv column {column}."
            )

    return df.set_index(
        "zone_id",
        drop=False,
    )


# ============================================================
# LOAD RISK BANDS
# ============================================================

@lru_cache(maxsize=1)
def load_risk_bands():
    """
    Load display risk-band configuration.
    """

    if not RISK_BANDS_FILE.exists():
        raise FileNotFoundError(
            f"Risk bands config not found:\n"
            f"{RISK_BANDS_FILE}"
        )

    with open(
        RISK_BANDS_FILE,
        "r",
        encoding="utf-8",
    ) as f:

        return json.load(f)


# ============================================================
# RAINFALL VALIDATION
# ============================================================

def validate_rainfall(
    rainfall: dict[str, Any]
) -> None:
    """
    Validate the four dynamic rainfall features.
    """

    missing = [
        feature
        for feature in DYNAMIC_FEATURES
        if feature not in rainfall
    ]

    if missing:

        raise ValueError(
            "Missing rainfall features:\n"
            + "\n".join(missing)
        )

    for feature in DYNAMIC_FEATURES:

        try:
            value = float(
                rainfall[feature]
            )

        except (
            TypeError,
            ValueError,
        ):

            raise ValueError(
                f"{feature} must be numeric."
            )

        if not np.isfinite(value):

            raise ValueError(
                f"{feature} must be finite."
            )

        if value < 0:

            raise ValueError(
                f"{feature} cannot be negative."
            )


# ============================================================
# RISK LEVEL
# ============================================================

def get_risk_level(
    probability: float
) -> str:
    """
    Convert continuous probability into
    the configured display risk band.
    """

    if not (
        np.isfinite(probability)
        and
        0.0 <= probability <= 1.0
    ):

        raise ValueError(
            f"Invalid probability: {probability}"
        )

    bands = load_risk_bands()

    for band_name in [
        "low",
        "moderate",
        "high",
        "very_high",
    ]:

        band = bands[band_name]

        lower = float(
            band["min"]
        )

        upper = float(
            band["max"]
        )

        if (
            probability >= lower
            and
            probability < upper
        ):

            return str(
                band["label"]
            )

    return "Very High"


# ============================================================
# STATIC SHAP EXPLANATION
# ============================================================

def get_static_shap_factors(
    model,
    X_static: pd.DataFrame,
    top_k: int = 5,
) -> list[dict[str, Any]]:
    """
    Generate top static SHAP factors for one prediction.
    """

    try:

        explainer = shap.TreeExplainer(
            model
        )

        shap_values = explainer.shap_values(
            X_static
        )

        # Handle different SHAP output formats.
        if isinstance(
            shap_values,
            list,
        ):

            values = np.asarray(
                shap_values[1]
            )[0]

        else:

            values = np.asarray(
                shap_values
            )

            if values.ndim == 3:

                values = values[
                    0,
                    :,
                    1
                ]

            elif values.ndim == 2:

                values = values[0]

            else:

                raise ValueError(
                    f"Unexpected SHAP shape: "
                    f"{values.shape}"
                )


        factors = []

        for feature, shap_value in zip(
            STATIC_FEATURES,
            values,
        ):

            shap_value = float(
                shap_value
            )

            if shap_value > 0:

                direction = (
                    "increases_risk"
                )

            elif shap_value < 0:

                direction = (
                    "decreases_risk"
                )

            else:

                direction = "neutral"


            factors.append({
                "feature":
                    feature,

                "shap_value":
                    shap_value,

                "abs_shap":
                    abs(shap_value),

                "direction":
                    direction,
            })


        factors.sort(
            key=lambda item:
                item["abs_shap"],
            reverse=True,
        )

        return factors[:top_k]


    except Exception as exc:

        return [{
            "feature":
                "SHAP_UNAVAILABLE",

            "shap_value":
                None,

            "abs_shap":
                None,

            "direction":
                "unknown",

            "error":
                str(exc),
        }]


# ============================================================
# MAIN PREDICTION FUNCTION
# ============================================================

def predict_risk(
    zone_id: str,
    rainfall_1d: float,
    rainfall_3d: float,
    rainfall_7d: float,
    rainfall_15d: float,
    include_explanations: bool = True,
) -> dict[str, Any]:
    """
    Run the complete GiriRakshak ML inference pipeline.

    Parameters
    ----------
    zone_id:
        Demo application zone ID.

    rainfall_1d:
        Cumulative rainfall over the previous 1 day.

    rainfall_3d:
        Cumulative rainfall over the previous 3 days.

    rainfall_7d:
        Cumulative rainfall over the previous 7 days.

    rainfall_15d:
        Cumulative rainfall over the previous 15 days.

    include_explanations:
        Whether to calculate SHAP and fusion explanations.

    Returns
    -------
    dict
        Continuous ML probabilities, risk score,
        risk level and optional explanations.
    """

    # --------------------------------------------------------
    # Validate zone ID
    # --------------------------------------------------------

    if (
        not isinstance(
            zone_id,
            str,
        )
        or
        not zone_id.strip()
    ):

        raise ValueError(
            "zone_id must be a non-empty string."
        )


    # --------------------------------------------------------
    # Validate rainfall
    # --------------------------------------------------------

    rainfall = {
        "rainfall_1d":
            rainfall_1d,

        "rainfall_3d":
            rainfall_3d,

        "rainfall_7d":
            rainfall_7d,

        "rainfall_15d":
            rainfall_15d,
    }

    validate_rainfall(
        rainfall
    )


    # --------------------------------------------------------
    # Load lookup tables
    # --------------------------------------------------------

    demo_zones = (
        load_demo_zones()
    )

    zones = (
        load_zone_features()
    )


    # --------------------------------------------------------
    # Resolve zone_id -> SU
    # --------------------------------------------------------

    if zone_id not in demo_zones.index:

        available = [
            str(x)
            for x in demo_zones.index
        ]

        raise ValueError(
            f"Unknown zone_id: {zone_id}. "
            f"Available demo zones: {available}"
        )


    demo_zone = (
        demo_zones.loc[
            zone_id
        ]
    )


    su = int(
        demo_zone["su"]
    )


    # --------------------------------------------------------
    # Resolve SU -> static feature vector
    # --------------------------------------------------------

    if su not in zones.index:

        raise ValueError(
            f"SU {su} for zone {zone_id} "
            "does not exist in zone_features.csv."
        )


    zone = (
        zones.loc[
            su
        ]
    )


    # --------------------------------------------------------
    # Build model frames
    # --------------------------------------------------------

    X_static = pd.DataFrame(
        [[
            float(zone[feature])
            for feature in STATIC_FEATURES
        ]],
        columns=STATIC_FEATURES,
    )


    X_dynamic = pd.DataFrame(
        [[
            float(
                rainfall[feature]
            )
            for feature in DYNAMIC_FEATURES
        ]],
        columns=DYNAMIC_FEATURES,
    )


    # --------------------------------------------------------
    # Static prediction
    # --------------------------------------------------------

    static_model = (
        load_static_model()
    )

    p_static = float(
        static_model
        .predict_proba(
            X_static
        )[0, 1]
    )


    # --------------------------------------------------------
    # Dynamic prediction
    # --------------------------------------------------------

    dynamic_model = (
        load_dynamic_model()
    )

    p_dynamic = float(
        dynamic_model
        .predict_proba(
            X_dynamic
        )[0, 1]
    )


    # --------------------------------------------------------
    # Fusion prediction
    # --------------------------------------------------------

    fusion = (
        load_fusion_model()
    )

    intercept = float(
        fusion["intercept"]
    )

    weight_static = float(
        fusion["weight_p_static"]
    )

    weight_dynamic = float(
        fusion["weight_p_dynamic"]
    )


    fusion_logit = (
        intercept
        +
        weight_static * p_static
        +
        weight_dynamic * p_dynamic
    )


    # Numerically stable sigmoid.
    if fusion_logit >= 0:

        exp_term = np.exp(
            -fusion_logit
        )

        p_final = float(
            1.0
            /
            (1.0 + exp_term)
        )

    else:

        exp_term = np.exp(
            fusion_logit
        )

        p_final = float(
            exp_term
            /
            (1.0 + exp_term)
        )


    # --------------------------------------------------------
    # Validate probabilities
    # --------------------------------------------------------

    probability_items = [
        (
            "p_static",
            p_static,
        ),
        (
            "p_dynamic",
            p_dynamic,
        ),
        (
            "p_final",
            p_final,
        ),
    ]


    for name, value in probability_items:

        if not (
            np.isfinite(value)
            and
            0.0 <= value <= 1.0
        ):

            raise ValueError(
                f"{name} is invalid: {value}"
            )


    # --------------------------------------------------------
    # Risk score + risk level
    # --------------------------------------------------------

    risk_score = float(
        p_final * 100.0
    )

    risk_level = (
        get_risk_level(
            p_final
        )
    )


    # --------------------------------------------------------
    # Core response
    # --------------------------------------------------------

    result = {
        "zone_id":
            zone_id,

        "p_static":
            p_static,

        "p_dynamic":
            p_dynamic,

        "p_final":
            p_final,

        "risk_score":
            risk_score,

        "risk_level":
            risk_level,
    }


    # --------------------------------------------------------
    # Explainability
    # --------------------------------------------------------

    if include_explanations:

        # Locked background means from final fusion analysis.
        background_static = 0.418235
        background_dynamic = 0.556300


        base_logit = (
            intercept
            +
            weight_static
            * background_static
            +
            weight_dynamic
            * background_dynamic
        )


        static_contribution = (
            weight_static
            *
            (
                p_static
                -
                background_static
            )
        )


        dynamic_contribution = (
            weight_dynamic
            *
            (
                p_dynamic
                -
                background_dynamic
            )
        )


        if (
            abs(static_contribution)
            >=
            abs(dynamic_contribution)
        ):

            dominant_signal = "P_static"

        else:

            dominant_signal = "P_dynamic"


        result[
            "top_factors"
        ] = get_static_shap_factors(
            static_model,
            X_static,
            top_k=5,
        )


        result[
            "fusion_contributions"
        ] = {
            "base_logit":
                float(base_logit),

            "static":
                float(
                    static_contribution
                ),

            "dynamic":
                float(
                    dynamic_contribution
                ),

            "dominant_signal":
                dominant_signal,
        }


    return result


# ============================================================
# CLI DEMO
# ============================================================

if __name__ == "__main__":

    print(
        json.dumps(
            predict_risk(
                zone_id="DEMO_ZONE_01",

                rainfall_1d=100.0,

                rainfall_3d=180.0,

                rainfall_7d=250.0,

                rainfall_15d=350.0,

                include_explanations=True,
            ),
            indent=2,
        )
    )

import sys
from pathlib import Path

import pytest


# Allow importing ml/src/predict.py
ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "ml" / "src"

sys.path.insert(0, str(SRC))

from predict import predict_risk


# ============================================================
# DEMO INPUT
# ============================================================

DEMO_INPUT = {
    "zone_id": "DEMO_ZONE_01",
    "rainfall_1d": 100.0,
    "rainfall_3d": 180.0,
    "rainfall_7d": 250.0,
    "rainfall_15d": 350.0,
}


# ============================================================
# BASIC OUTPUT TEST
# ============================================================

def test_prediction_output():

    result = predict_risk(
        **DEMO_INPUT,
        include_explanations=True
    )

    assert "p_static" in result
    assert "p_dynamic" in result
    assert "p_final" in result

    assert "risk_score" in result
    assert "risk_level" in result

    assert "top_factors" in result
    assert "fusion_contributions" in result


# ============================================================
# PROBABILITY RANGE
# ============================================================

def test_probabilities_are_continuous_and_valid():

    result = predict_risk(
        **DEMO_INPUT,
        include_explanations=False
    )

    for key in [
        "p_static",
        "p_dynamic",
        "p_final",
    ]:

        value = result[key]

        assert isinstance(
            value,
            float
        )

        assert 0.0 <= value <= 1.0


# ============================================================
# RISK SCORE RANGE
# ============================================================

def test_risk_score_range():

    result = predict_risk(
        **DEMO_INPUT,
        include_explanations=False
    )

    assert isinstance(
        result["risk_score"],
        float
    )

    assert 0.0 <= result["risk_score"] <= 100.0

    # Risk score must be P_final * 100
    assert abs(
        result["risk_score"]
        -
        result["p_final"] * 100.0
    ) < 1e-10


# ============================================================
# RISK LEVEL
# ============================================================

def test_risk_level_is_valid():

    result = predict_risk(
        **DEMO_INPUT,
        include_explanations=False
    )

    assert result["risk_level"] in {
        "Low",
        "Moderate",
        "High",
        "Very High",
    }


# ============================================================
# SHAP OUTPUT
# ============================================================

def test_static_shap_output():

    result = predict_risk(
        **DEMO_INPUT,
        include_explanations=True
    )

    factors = result["top_factors"]

    assert isinstance(
        factors,
        list
    )

    assert len(factors) > 0

    # Normal successful case
    if factors[0]["feature"] != "SHAP_UNAVAILABLE":

        assert len(factors) <= 5

        for factor in factors:

            assert "feature" in factor
            assert "shap_value" in factor
            assert "abs_shap" in factor
            assert "direction" in factor


# ============================================================
# FUSION OUTPUT
# ============================================================

def test_fusion_contributions():

    result = predict_risk(
        **DEMO_INPUT,
        include_explanations=True
    )

    fusion = result[
        "fusion_contributions"
    ]

    assert "base_logit" in fusion
    assert "static" in fusion
    assert "dynamic" in fusion
    assert "dominant_signal" in fusion

    assert fusion[
        "dominant_signal"
    ] in {
        "P_static",
        "P_dynamic",
    }


# ============================================================
# UNKNOWN ZONE
# ============================================================

def test_unknown_zone_fails():

    with pytest.raises(
        ValueError,
        match="Unknown zone_id"
    ):

        predict_risk(
            zone_id="DOES-NOT-EXIST",
            rainfall_1d=100.0,
            rainfall_3d=180.0,
            rainfall_7d=250.0,
            rainfall_15d=350.0,
        )


# ============================================================
# NEGATIVE RAINFALL
# ============================================================

def test_negative_rainfall_fails():

    with pytest.raises(
        ValueError
    ):

        predict_risk(
            zone_id="DEMO_ZONE_01",
            rainfall_1d=-1.0,
            rainfall_3d=180.0,
            rainfall_7d=250.0,
            rainfall_15d=350.0,
        )


# ============================================================
# DETERMINISM
# ============================================================

def test_same_input_same_output():

    result1 = predict_risk(
        **DEMO_INPUT,
        include_explanations=False
    )

    result2 = predict_risk(
        **DEMO_INPUT,
        include_explanations=False
    )

    import math

    assert result1["zone_id"] == result2["zone_id"]

    assert math.isclose(
        result1["p_static"],
        result2["p_static"],
        rel_tol=1e-12,
        abs_tol=1e-12
    )

    assert math.isclose(
        result1["p_dynamic"],
        result2["p_dynamic"],
        rel_tol=1e-12,
        abs_tol=1e-12
    )

    assert math.isclose(
        result1["p_final"],
        result2["p_final"],
        rel_tol=1e-12,
        abs_tol=1e-12
    )

    assert math.isclose(
        result1["risk_score"],
        result2["risk_score"],
        rel_tol=1e-12,
        abs_tol=1e-12
    )

    assert result1["risk_level"] == result2["risk_level"]

# ============================================================
# FINAL
# ============================================================

if __name__ == "__main__":

    pytest.main(
        [
            __file__,
            "-v"
        ]
    )

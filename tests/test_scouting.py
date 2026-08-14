"""Tests for the draft models and the scouting layer.

The dangerous failure here is silent: a permuted feature vector, or a model
loaded against a changed feature list, still returns confident numbers. So the
first thing tested is the feature contract, then a handful of pinned predictions
that would move if anything upstream drifted.
"""

import json
import pathlib
import sys

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from ncaa_bbStats import features as F  # noqa: E402
from ncaa_bbStats._paths import data_path  # noqa: E402

xgboost = pytest.importorskip("xgboost", reason="needs the model extra")

from ncaa_bbStats import scouting  # noqa: E402


MODELS_PRESENT = pathlib.Path(data_path("models", "manifest.json")).is_file()
requires_models = pytest.mark.skipif(
    not MODELS_PRESENT, reason="no trained models; run model_store"
)


# --- the feature contract ------------------------------------------------

def test_feature_lists_have_no_duplicates():
    for stage in (1, 2):
        features = F.model_features(stage)
        duplicates = {f for f in features if features.count(f) > 1}
        assert not duplicates, f"stage {stage} lists {duplicates} twice"


def test_stage2_extends_stage1():
    """Stage 2 adds biography on top of Stage 1's features, in the same order."""
    stage1 = F.model_features(1)
    stage2 = F.model_features(2)
    assert stage2[: len(stage1)] == stage1


def test_bio_features_are_stage2_only():
    """Biography comes from the draft record, so using it in Stage 1 leaks the label."""
    stage1 = F.model_features(1)
    assert not (set(F.BIO_FEATURES) & set(stage1))


def test_align_produces_float_columns_in_order():
    """XGBoost cannot consume pandas NA; align must coerce it to NaN."""
    import numpy as np
    import pandas as pd

    frame = pd.DataFrame([{"age": 21, "extra": 5, "nullable": pd.NA}])
    features = ["age", "nullable", "missing_entirely"]
    aligned = F.align(frame, features)

    assert list(aligned.columns) == features
    assert aligned.dtypes.unique().tolist() == [np.dtype("float64")]
    assert np.isnan(aligned.iloc[0]["nullable"])
    assert np.isnan(aligned.iloc[0]["missing_entirely"])


@requires_models
def test_manifest_matches_the_current_feature_lists():
    """A model scored on a permuted vector returns confident garbage.

    Both the loader and this test check it; if the feature list changes, retrain.
    """
    with open(data_path("models", "manifest.json"), encoding="utf-8") as f:
        manifest = json.load(f)
    for stage in (1, 2):
        assert manifest[f"stage{stage}"]["features"] == F.model_features(stage)


@requires_models
def test_models_load():
    assert scouting._model(1) is not None
    assert scouting._model(2) is not None


# --- predictions ---------------------------------------------------------

@requires_models
def test_probability_is_high_for_a_top_pick():
    """Kade Anderson went 3rd overall in 2025."""
    probability = scouting.predict_draft_probability("Kade Anderson", 2025)
    assert probability is not None
    assert probability > 0.8


@requires_models
def test_probability_is_a_probability():
    for name in ("Kade Anderson", "Jac Caglianone"):
        value = scouting.predict_draft_probability(name)
        if value is not None:
            assert 0.0 <= value <= 1.0


@requires_models
def test_unknown_player_returns_none():
    assert scouting.predict_draft_probability("Nobody At All") is None
    assert scouting.scouting_report("Nobody At All") is None
    assert scouting.is_draft_eligible("Nobody At All") is None


@requires_models
def test_predicted_order_is_never_below_one():
    """The regressor is unbounded; a standout otherwise extrapolates past pick 1."""
    board = scouting.draft_board(2025, n=50)
    orders = [b["predicted_order"] for b in board if b["predicted_order"]]
    assert orders
    assert min(orders) >= 1.0


@requires_models
def test_draft_board_is_ranked_and_finds_real_draftees():
    board = scouting.draft_board(2025, n=25)
    assert [b["rank"] for b in board] == list(range(1, 26))
    probabilities = [b["draft_probability"] for b in board]
    assert probabilities == sorted(probabilities, reverse=True)
    # The top of the board should be dominated by players who were drafted.
    drafted = sum(1 for b in board if b["actual_pick"])
    assert drafted >= 15, f"only {drafted} of the top 25 were actually drafted"


@requires_models
def test_order_is_suppressed_below_the_threshold():
    """The order model is trained only on drafted players."""
    board = scouting.draft_board(2025, n=2000)
    for entry in board:
        if entry["draft_probability"] < scouting.MIN_PROBABILITY_FOR_ORDER:
            assert entry["predicted_order"] is None


# --- eligibility ---------------------------------------------------------

@requires_models
def test_eligibility_returns_a_basis_not_just_a_bool():
    """Eligibility is inferred, so the evidence used has to be visible."""
    result = scouting.is_draft_eligible("Kade Anderson", 2025)
    assert result is not None
    eligible, basis = result
    assert eligible is True
    assert basis in {"drafted", "class", "age", "unknown", "ineligible"}


@requires_models
def test_drafted_players_are_never_filtered_out_as_ineligible():
    """The 'drafted' basis must be checked first or positives get deleted."""
    import pandas as pd

    matrix = scouting._matrix()
    drafted = matrix[matrix["drafted"] == 1]
    assert len(drafted) > 1000
    assert drafted["eligible"].all()
    assert (drafted["eligibility_basis"] == "drafted").all()


# --- explanations --------------------------------------------------------

@requires_models
def test_explanation_reports_which_method_it_used():
    explanation = scouting.explain_prediction("Kade Anderson", 2025)
    assert explanation["method"] in {"shap", "gain"}
    assert explanation["strengths"] and explanation["concerns"]
    assert all(e["impact"] > 0 for e in explanation["strengths"])
    assert all(e["impact"] < 0 for e in explanation["concerns"])


@requires_models
def test_gain_fallback_works_without_shap():
    explanation = scouting.explain_prediction("Kade Anderson", 2025, method="gain")
    assert explanation["method"] == "gain"
    assert explanation["strengths"]


# --- exact contributions -------------------------------------------------
#
# Every one of these is really the same assertion: the bars a caller draws have
# to land on the number printed above them. An attribution that is 99% right is
# a chart that does not reach its own total.

@requires_models
def test_contributions_sum_to_the_prediction():
    pytest.importorskip("shap", reason="needs the explain extra")
    for stage in (1, 2):
        result = scouting.feature_contributions("Kade Anderson", 2025, stage=stage)
        total = result["base"] + sum(
            c["contribution"] for c in result["contributions"]
        )
        assert total == pytest.approx(result["prediction"], abs=1e-9)


@requires_models
def test_stage1_contributions_are_log_odds():
    pytest.importorskip("shap", reason="needs the explain extra")
    result = scouting.feature_contributions("Kade Anderson", 2025, stage=1)
    assert result["units"] == "log-odds"
    assert scouting._expit(result["prediction"]) == pytest.approx(
        scouting.predict_draft_probability("Kade Anderson", 2025), abs=1e-6
    )


@requires_models
def test_stage2_contributions_are_draft_order():
    pytest.importorskip("shap", reason="needs the explain extra")
    result = scouting.feature_contributions("Kade Anderson", 2025, stage=2)
    assert result["units"] == "draft order"
    # The base is the average pick the regressor starts everyone from.
    assert 50 < result["base"] < 400
    assert result["prediction"] == pytest.approx(
        scouting.predict_draft_order("Kade Anderson", 2025), abs=1e-3
    )


@requires_models
def test_contributions_cover_every_feature_largest_first():
    pytest.importorskip("shap", reason="needs the explain extra")
    for stage in (1, 2):
        result = scouting.feature_contributions("Kade Anderson", 2025, stage=stage)
        entries = result["contributions"]
        assert {c["feature"] for c in entries} == set(F.model_features(stage))
        magnitudes = [abs(c["contribution"]) for c in entries]
        assert magnitudes == sorted(magnitudes, reverse=True)


@requires_models
def test_contributions_keep_features_that_were_never_supplied():
    """A missing input is routed down a learned default branch, so it counts.

    Dropping the NaN-valued entries -- which is what explain_prediction does for
    its shortlist -- would break the sum on exactly the sparse rows that most
    need explaining.
    """
    pytest.importorskip("shap", reason="needs the explain extra")
    scored = scouting.predict_from_stats(
        "pitcher", 21, {"era_pitch": 2.40, "so_pitch": 130}, season=2025,
    )
    result = scouting.feature_contributions(features=scored["feature_row"])
    unsupplied = [c for c in result["contributions"] if c["value"] is None]
    assert len(unsupplied) > 30, "a two-stat line should leave most fields unset"
    assert any(c["contribution"] != 0 for c in unsupplied)
    total = result["base"] + sum(c["contribution"] for c in result["contributions"])
    assert total == pytest.approx(result["prediction"], abs=1e-9)


@requires_models
def test_a_custom_stat_line_explains_the_prediction_it_returned():
    pytest.importorskip("shap", reason="needs the explain extra")
    scored = scouting.predict_from_stats(
        "pitcher", 21,
        {"era_pitch": 2.40, "so_pitch": 130, "bb_pitch": 25, "ip_pitch": 95.0},
        team="LSU", season=2025,
    )
    assert set(scored["feature_row"]) == set(F.model_features(2))

    stage1 = scouting.feature_contributions(features=scored["feature_row"], stage=1)
    assert scouting._expit(stage1["prediction"]) == pytest.approx(
        scored["draft_probability"], abs=1e-6
    )
    stage2 = scouting.feature_contributions(features=scored["feature_row"], stage=2)
    assert stage2["prediction"] == pytest.approx(
        scored["predicted_order"], abs=1e-3
    )


@requires_models
def test_contributions_for_an_unknown_player_are_none():
    pytest.importorskip("shap", reason="needs the explain extra")
    assert scouting.feature_contributions("Nobody At All", 2025) is None


@requires_models
def test_scouting_report_is_readable_and_honest():
    report = scouting.scouting_report("Kade Anderson", 2025)
    assert "Kade Anderson" in report
    assert "Draft grade" in report
    assert "LSU" in report
    # It must say where the explanation came from.
    assert "shap" in report.lower() or "gain" in report.lower()


# --- custom input --------------------------------------------------------

@requires_models
def test_predict_from_stats_accepts_a_partial_line():
    result = scouting.predict_from_stats(
        "pitcher", 21,
        {"era_pitch": 2.40, "so_pitch": 130, "bb_pitch": 25, "ip_pitch": 95.0},
        team="LSU", season=2025,
    )
    assert 0.0 <= result["draft_probability"] <= 1.0
    assert result["confidence"] in {"low", "medium", "high"}
    assert result["report"]


@requires_models
def test_predict_from_stats_flags_how_much_was_imputed():
    """A four-statistic line is not the same evidence as a full season."""
    sparse = scouting.predict_from_stats(
        "batter", 21, {"hr_bat": 10}, season=2025
    )
    assert sparse["confidence"] == "low"
    assert len(sparse["supplied_features"]) < 5


@requires_models
def test_better_lines_score_higher():
    """A sanity check that the model responds to the input at all."""
    strong = scouting.predict_from_stats(
        "pitcher", 21,
        {"era_pitch": 1.80, "so_pitch": 150, "bb_pitch": 15, "ip_pitch": 100.0,
         "h_pitch": 60, "hr_pitch": 3, "g_pitch": 16, "gs_pitch": 16},
        team="LSU", season=2025,
    )
    weak = scouting.predict_from_stats(
        "pitcher", 19,
        {"era_pitch": 7.50, "so_pitch": 12, "bb_pitch": 20, "ip_pitch": 18.0,
         "h_pitch": 30, "hr_pitch": 6, "g_pitch": 9, "gs_pitch": 1},
        team="LSU", season=2025,
    )
    assert strong["draft_probability"] > weak["draft_probability"]


@requires_models
def test_unsuffixed_stat_names_are_routed_by_role():
    """A caller should not have to know about the _bat/_pitch suffixes."""
    result = scouting.predict_from_stats(
        "pitcher", 21, {"era": 2.40, "so": 130, "ip": 95.0}, season=2025
    )
    assert "era_pitch" in result["supplied_features"]
    assert "so_pitch" in result["supplied_features"]


# --- the model card ------------------------------------------------------

@requires_models
def test_model_card_reports_held_out_metrics():
    card = scouting.model_card()
    assert card["stage1"]["metrics"]["pr_auc"] > 0.5
    assert card["stage1"]["metrics"]["roc_auc"] > 0.85
    assert card["stage2"]["metrics"]["spearman"] > 0.4
    assert card["test_year"] not in card["train_years"]


@requires_models
def test_model_card_states_the_limitations():
    card = scouting.model_card()
    assert len(card["limitations"]) >= 4
    text = " ".join(card["limitations"]).lower()
    assert "base rate" in text
    assert "inferred" in text or "estimated" in text


@requires_models
def test_model_card_does_not_claim_the_reference_numbers():
    """V7's published numbers are not this model's numbers."""
    card = scouting.model_card()
    reference = card["reference_implementation"]
    assert "NOT this model" in reference["note"]
    assert reference["stage1_pr_auc"] != card["stage1"]["metrics"]["pr_auc"]
    assert reference["stage2_spearman"] != card["stage2"]["metrics"]["spearman"]


@requires_models
def test_model_card_declares_its_lineage():
    """A separate lineage has to say so, and say what differs.

    The failure this prevents is a quiet one: a model named after V7, serving
    numbers V7's paper does not describe, with nothing on the card that would
    let a reader tell the two apart.
    """
    card = scouting.model_card()
    lineage = card["lineage"]
    assert "not a patched" in lineage["relationship"]
    assert len(lineage["differences"]) >= 5

    text = " ".join(lineage["differences"]).lower()
    for topic in ("features", "labels", "hyperparameters"):
        assert topic in text, f"lineage does not mention {topic}"


@requires_models
def test_stage_three_is_documented_as_not_shipped():
    card = scouting.model_card()
    assert card["stage3"]["shipped"] is False
    assert "0.003" in card["stage3"]["reason"]


# --- graceful degradation ------------------------------------------------

def test_importing_the_package_does_not_load_xgboost():
    """Predictions are opt-in; the base import must stay light."""
    import subprocess

    program = (
        "import sys; sys.path.insert(0, %r); "
        "import ncaa_bbStats; "
        "assert 'xgboost' not in sys.modules, 'xgboost imported eagerly'; "
        "assert 'shap' not in sys.modules, 'shap imported eagerly'; "
        "print('ok')" % str(REPO_ROOT / "src")
    )
    result = subprocess.run(
        [sys.executable, "-c", program], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr[-800:]

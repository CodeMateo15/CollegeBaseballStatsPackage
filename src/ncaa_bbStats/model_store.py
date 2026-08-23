"""Build the training matrix and fit the draft models.

Run as a script; importing this module has no side effects.

    python -m ncaa_bbStats.model_store --matrix        # build the matrix only
    python -m ncaa_bbStats.model_store                 # build, train, save

Two models ship:

- **Stage 1** classifies whether a player-season leads to being drafted.
- **Stage 2** orders the drafted players within a class.

A third stage -- predicting a signing bonus as a share of slot value -- was
attempted and is **not shipped**. It scored a rank correlation of 0.003 against
held-out data, which is noise with a ``.predict()`` method. What is genuinely
useful there is the denominator: slot values are published facts, available as
:func:`ncaa_bbStats.draft_detail_utils.slot_value`.

Requires the ``model`` extra (``pip install "ncaa_bbStats[model]"``).
"""

import argparse
import gzip
import hashlib
import json
import os
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from ncaa_bbStats import features as F
from ncaa_bbStats._paths import data_path
from ncaa_bbStats.team_registry import as_team_id

# Validation is leave-one-season-out: for each season, a model fitted on every
# other season predicts it. There is no single held-out year any more, and that
# is the point -- the public matrix has no future season to hold out, and a
# board shown for a season the model trained on reports the model's memory. Its
# rank correlation came out at 0.99, against 0.65 on genuinely unseen data.
#
# The seasons come from the matrix rather than a constant here, so adding one is
# a data change and not a code change.

STAGE1_PARAMS = dict(
    n_estimators=400, learning_rate=0.05, max_depth=6, subsample=0.8,
    colsample_bytree=0.8, random_state=0,
)
STAGE2_PARAMS = dict(
    n_estimators=600, learning_rate=0.03, max_depth=4, subsample=0.8,
    colsample_bytree=0.7, min_child_weight=5, reg_alpha=1.0, reg_lambda=5.0,
    random_state=0,
)

# V8-public: the same two-stage design, refitted on the public NCAA matrix. The
# training data changed outright -- different source, different population,
# different experience features -- so this is a new version rather than a
# revision of v7-public, and v7-public's numbers do not describe it.
MODEL_VERSION = "v8-public-2026.1"

# What differs from the published V7, so a number from one is never quoted for
# the other. Surfaced through model_card().
LINEAGE = {
    "derived_from": "V7 (Biggs & Gerber 2026), three-stage XGBoost",
    "relationship": "separate lineage, not a patched V7",
    "differences": [
        "Inputs: every column comes from the public combined matrix built from "
        "NCAA-published statistics. The nine vendor-proprietary metrics V7 used "
        "(wRC+, wOBA, wRAA, wRC, wSB, Spd, FIP, E-F, LOB%) are recomputed from "
        "NCAA counting statistics with college-fitted constants. They correlate "
        "with the vendor's at r = 0.93-0.999 but are not equal to them, so the "
        "model had to be refitted and not merely re-pointed.",
        "No age. NCAA publishes no date of birth, so the age feature V7 used is "
        "replaced by class standing, seasons elapsed since a player's first "
        "appearance, and the class they arrived in. Draft eligibility is decided "
        "the same way, without the age-21 branch.",
        "Stages: two are shipped. V7 also fitted signing-bonus and slot-value "
        "regressors; the bonus/slot ratio scored a rank correlation of 0.003 "
        "on held-out data here, so it is not shipped. The five biography "
        "columns V7's order model read off the draft record are also gone: they "
        "existed only for players already drafted, which is the label Stage 1 "
        "predicts.",
        "Labels: draft records are matched to careers independently here, from "
        "the public draft feed, rather than reusing V7's matching.",
        "Population: 61,270 Division I player-seasons with no playing-time "
        "minimum and no eligibility filter, against 20,220 rows in "
        "V7's matrix. V7 was fitted on a vendor's qualified leaderboards; "
        "qualification is a function of playing time, which is a function of "
        "perceived quality, so filtering on it selects on the outcome and drops "
        "roughly a quarter of real draftees. Base rates therefore differ (4.2% "
        "here) and precision figures are not comparable between the two.",
        "Validation: leave-one-season-out across 2021-2026, where V7 held out a "
        "single season. Every figure reported here is out-of-fold, and the "
        "board served for a season is the prediction of the model that did not "
        "train on it.",
        "Seasons 2021-2026. 2026 was scraped live from stats.ncaa.org rather "
        "than taken from the public mirror, which stopped updating mid-season "
        "in April 2026; it covers all 308 Division I team-seasons.",
        "Hyperparameters are this package's, not V7's, so a V7-to-V8-public "
        "comparison reflects features, labels, population, split and settings "
        "together rather than any one of them.",
    ],
}


def _require_xgboost():
    try:
        import xgboost  # noqa: F401
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise ImportError(
            "Training the draft models needs XGBoost: "
            'pip install "ncaa_bbStats[model]"'
        ) from exc
    return xgboost


# --- matrix construction -------------------------------------------------
#
# The matrix is no longer assembled here from a dozen caches. It is read from
# the public combined matrix built by the research repo's
# `csv_editing_scripts/build_public_combined.py`, which joins NCAA-published
# player statistics to team statistics, RPI and the EADA finance survey. A copy
# ships with the package so a fit is reproducible from the wheel alone, and so
# every input to the shipped model is redistributable -- which the FanGraphs
# export the previous matrix was built from was not.

# The no-minimum cut, not the qualified one. A playing-time filter selects on a
# variable that is itself a function of perceived quality -- the thing Stage 1
# predicts -- so it is selection on the outcome, and it removed 510 of the 2,109 (2021-25)
# drafted players, non-randomly. Measured on the players the qualified cut keeps,
# fitting on the wider population costs 0.003 PR-AUC and 0.002 Spearman, which
# is well inside seed noise. The qualified subset is recoverable from this fit by
# filtering; the reverse is not possible.
PUBLIC_MATRIX = "batting_pitching_combined_with_rpi_public_v2_nomin.csv.gz"

# Columns the public matrix spells differently from :mod:`ncaa_bbStats.features`.
# The nine run-value metrics are the interesting ones: the public matrix
# recomputes them from NCAA counting statistics with college-fitted constants,
# so they are the rebuilt versions the `c` prefix denotes, published without it.
_RENAME = {
    "fip_pitch": "cfip_pitch",
    "lob%_pitch": "clob%_pitch",
    "e-f_pitch": "e-cf_pitch",
    "woba_bat": "cwoba_bat",
    "wraa_bat": "cwraa_bat",
    "wrc_bat": "cwrc_bat",
    "wrc+_bat": "cwrc+_bat",
    "wsb_bat": "cwsb_bat",
    "spd_bat": "cspd_bat",
    # RPI. These three are ranks, not rates, despite the bare names.
    "rpi_team": "rpi_rank_team",
    "SOS_team": "sos_rank_team",
    "NC_RPI_team": "nonconference_rpi_rank_team",
    "Q1_Wins_team": "q1_wins_team",
}
_RENAME.update({
    f"{stem}_eada_team": f"{stem}_team" for stem in (
        "budget_pct", "log_budget", "opex_per_player_pct",
        "log_budget_per_player", "roster_size", "log_revenue", "net_revenue",
        "coaching_staff_size", "dept_recruiting_pct", "log_dept_coach_salary",
    )
})

# Win rates the public matrix stores as "12-11" strings. The paired numeric
# wins/losses columns beside them are what to read; parsing the string would
# work today and break the first time a tie appears in it.
_WIN_PCT = {
    "conference_win_pct_team": "Conference_Record",
    "nonconference_win_pct_team": "NC_Rec",
    "home_win_pct_team": "Home",
    "road_win_pct_team": "Road",
    "neutral_win_pct_team": "Neutral",
    "q1_win_pct_team": "Q1",
    "q2_win_pct_team": "Q2",
    "q3_win_pct_team": "Q3",
    "q4_win_pct_team": "Q4",
}


def _public_matrix_path() -> str:
    return data_path("public_matrix", PUBLIC_MATRIX)


def build_matrix(path: str | None = None) -> pd.DataFrame:
    """Read the public combined matrix and put it in the model's vocabulary.

    Args:
        path (str, optional): Override the packaged copy.

    Returns:
        pandas.DataFrame: One row per player-season, with the draft label,
        the eligibility verdict and every column :func:`features.model_features`
        asks for.
    """
    path = path or _public_matrix_path()
    if not os.path.isfile(path):
        raise FileNotFoundError(
            f"No public matrix at {path}. It ships with the package; if you are "
            "working from a source checkout, build it with the research repo's "
            "csv_editing_scripts/build_public_combined.py."
        )
    df = pd.read_csv(path, low_memory=False)

    # Role. The public matrix spells these "Two-Way"/"Pitcher"/"Batter".
    df["role"] = (df["role"].astype(str).str.strip().str.lower()
                            .str.replace("-", "_", regex=False).map(F.ROLE_MAP))

    # Total bases is a feature but not a published column; it is exact from the
    # hit breakdown, so derive rather than drop it.
    df["tb_bat"] = (df["1b_bat"].fillna(0) + 2 * df["2b_bat"].fillna(0)
                    + 3 * df["3b_bat"].fillna(0) + 4 * df["hr_bat"].fillna(0))
    # ...but only where the player actually batted. Filling the components with
    # zero above would otherwise hand every pitcher a real-looking 0.
    df.loc[df["ab_bat"].isna(), "tb_bat"] = np.nan

    # A winless team has an undefined Pythagorean ratio, not an infinite one.
    # The public builder divides by the win rate under `errstate(divide=...)`
    # and lets the inf through; 22 rows carry one, and XGBoost refuses the
    # matrix outright rather than treating it as missing.
    df["PE_pct_team"] = df["PE_pct_team"].replace([np.inf, -np.inf], np.nan)

    # Wins over decided games, which is what the other *_win_pct_team features
    # measure. Not WPCT_team: that is the published percentage and counts ties,
    # so setting them equal made two features perfectly collinear (r = 1.000)
    # while discarding the distinction on the 1,457 rows that have a tie.
    _w = pd.to_numeric(df["W_team"], errors="coerce")
    _l = pd.to_numeric(df["L_team"], errors="coerce")
    df["overall_win_pct_team"] = _w / (_w + _l).replace(0, np.nan)
    for feature, stem in _WIN_PCT.items():
        wins = pd.to_numeric(df[f"{stem}_Wins_team"], errors="coerce")
        losses = pd.to_numeric(df[f"{stem}_Losses_team"], errors="coerce")
        played = wins + losses
        df[feature] = wins / played.replace(0, np.nan)

    # Renaming last: `Q1_Wins_team` is both a rename source and a win-rate
    # input, and doing it first leaves the loop above looking for a column that
    # has already been renamed out from under it.
    df = df.rename(columns=_RENAME)

    F.add_usage_features(df)

    # Draft label. The public matrix carries one row per player-season and
    # records the pick only against the season that produced it, so a non-null
    # pick is exactly "drafted out of this season".
    df["draft_pick"] = pd.to_numeric(df["Pick"], errors="coerce")
    df["draft_round"] = pd.to_numeric(df["Round"], errors="coerce")
    df["drafted"] = df["draft_pick"].notna().astype(int)
    df["draft_year"] = df["year"].where(df["drafted"] == 1)

    # Identity. `person_id` is the public matrix's cross-season key -- NCAA
    # re-mints its per-season player id every year, so `playerid` cannot group a
    # career and `person_id` is what the research repo's record linkage built to
    # replace it.
    df["player_id"] = df["person_id"]
    df["team_id"] = df["team"].map(lambda t: as_team_id(str(t)))
    df["division"] = df.get("division_team")

    df["eligibility_basis"] = [
        _eligibility_basis(drafted, class_ord, seasons)
        for drafted, class_ord, seasons in zip(
            df["drafted"], df["class_ord"], df["seasons_elapsed"]
        )
    ]
    # Everyone is scored. See the note above ELIGIBLE_BASES.
    df["eligible"] = True

    return df


# Draft eligibility. MLB rules make a college player eligible after their
# junior year, or on turning 21 near the draft. The second half of that is
# unknowable here: NCAA publishes no date of birth.
#
# So there is no eligibility filter any more, and that is a correctness fix
# rather than a simplification. The previous rule read
#
#     if drafted: return "drafted"     # <- the label decided membership
#
# ahead of the class and tenure tests, which meant 413 of 2,565 drafted rows
# (16.1%) entered the training population *only because they were positive*.
# Inside that population `class_ord < 3 and seasons_elapsed < 2` selected 412
# rows of which 412 were drafted -- a perfectly separating rule built from two
# columns that are themselves Stage 1 features. It inflated every reported
# metric, and at inference on an unlabelled season the same players were simply
# filtered out, so the board structurally could not surface an early-eligible
# draftee. There are roughly 69 of those a year.
#
# Dropping the `drafted` branch alone would have excluded those 413 players
# instead, which trades a leak for a blind spot. Scoring the whole population
# keeps them and lets the model learn eligibility from class and tenure, which
# it can: both are features. The base rate falls to 4.2% and Stage 1 precision
# figures fall with it -- that is the honest number, not a regression.
CLASS_ELIGIBLE_SEASONS = 3
ELIGIBLE_BASES = ("scored",)


def _eligibility_basis(drafted, class_ord, seasons_elapsed):
    """Retained for the manifest and for is_draft_eligible()'s basis string.

    Describes a player-season; it no longer gates the population. Note the
    ordering: `drafted` is reported first because being drafted is proof of
    eligibility, but that is a statement about the past, not a filter.
    """
    if drafted:
        return "drafted"
    if pd.notna(class_ord) and class_ord >= CLASS_ELIGIBLE_SEASONS:
        return "class"
    # `seasons_elapsed` counts from a player's first appearance, so it is 0 in
    # their first season and 2 in their third. The threshold is one less than
    # the season count for that reason, not by an off-by-one.
    if pd.notna(seasons_elapsed) and seasons_elapsed >= CLASS_ELIGIBLE_SEASONS - 1:
        return "tenure"
    if pd.isna(class_ord) and pd.isna(seasons_elapsed):
        return "unknown"
    return "early-or-ineligible"


# --- training ------------------------------------------------------------

FOLDS_DIR = "folds"


def _college_draft_order(eligible: pd.DataFrame) -> pd.DataFrame:
    """The drafted rows, ordered within their season. Stage 2's population."""
    drafted = eligible[eligible["drafted"] == 1].copy()
    drafted = drafted.sort_values(["year", "draft_pick"])
    drafted["college_draft_order"] = drafted.groupby("year").cumcount() + 1
    return drafted


def _fit_stage1(xgb, rows):
    model = xgb.XGBClassifier(**STAGE1_PARAMS)
    model.fit(F.align(rows, F.model_features(1)).astype(float), rows["drafted"])
    return model


def _fit_stage2(xgb, rows):
    model = xgb.XGBRegressor(**STAGE2_PARAMS, eval_metric="mae")
    model.fit(F.align(rows, F.model_features(2)).astype(float),
              rows["college_draft_order"])
    return model


def train(matrix: pd.DataFrame, out_dir: str) -> dict:
    """Fit both stages leave-one-season-out, plus a full-data pair.

    For each season, a model fitted on every *other* season predicts it. Those
    out-of-fold predictions are the only ones this package will report for a
    season it has labels for, because a prediction from a model that trained on
    the row is not a prediction -- it is recall, and it scored 0.99 where honest
    work scores 0.65.

    A pair fitted on everything is also written, under the names the loader
    reaches for by default. That is the model for a season with no labels yet
    and for a stat line somebody types in; it is never used to score a season
    that has a fold of its own.

    Args:
        matrix (pandas.DataFrame): Output of :func:`build_matrix`.
        out_dir (str): Where the artifacts go.

    Returns:
        dict: The manifest, also written to ``manifest.json``.
    """
    xgb = _require_xgboost()
    from sklearn.metrics import average_precision_score, roc_auc_score
    from scipy.stats import spearmanr

    folds_dir = os.path.join(out_dir, FOLDS_DIR)
    os.makedirs(folds_dir, exist_ok=True)

    eligible = matrix[matrix["eligible"]].copy()
    drafted = _college_draft_order(eligible)
    seasons = sorted(int(y) for y in eligible["year"].unique())

    # Out-of-fold predictions, indexed like the frames they come from so they
    # can be written back onto the matrix without a join.
    oof_probability = pd.Series(np.nan, index=eligible.index, dtype=float)
    # Indexed over every eligible row, not just the drafted ones. Stage 2 is
    # *fitted* on drafted players -- that is where a true order exists -- but it
    # has to be *applied* to everybody, because the board ranks undrafted
    # players too. Storing it only for the drafted rows would hand every drafted
    # player a projected order and leave the rest blank, which puts the label
    # itself on the board for anyone who notices the pattern.
    oof_order = pd.Series(np.nan, index=eligible.index, dtype=float)
    per_season = {}

    for season in seasons:
        s1_train = eligible[eligible["year"] != season]
        s1_test = eligible[eligible["year"] == season]
        stage1 = _fit_stage1(xgb, s1_train)
        probabilities = stage1.predict_proba(
            F.align(s1_test, F.model_features(1)).astype(float))[:, 1]
        oof_probability.loc[s1_test.index] = probabilities

        s2_train = drafted[drafted["year"] != season]
        stage2 = _fit_stage2(xgb, s2_train)
        # Same floor the inference path applies: there is no zeroth pick.
        oof_order.loc[s1_test.index] = np.clip(
            stage2.predict(F.align(s1_test, F.model_features(2)).astype(float)),
            1.0, None)

        # Scored only where a true order exists, which is the drafted subset.
        s2_test = drafted[drafted["year"] == season]
        predicted = oof_order.loc[s2_test.index].to_numpy(dtype=float)
        rho, p_value = spearmanr(predicted, s2_test["college_draft_order"])
        per_season[str(season)] = {
            "stage1": {
                "pr_auc": round(float(average_precision_score(
                    s1_test["drafted"], probabilities)), 4),
                "roc_auc": round(float(roc_auc_score(
                    s1_test["drafted"], probabilities)), 4),
                "base_rate": round(float(s1_test["drafted"].mean()), 4),
                "n_train": int(len(s1_train)),
                "n_test": int(len(s1_test)),
            },
            "stage2": {
                "spearman": round(float(rho), 4),
                "p_value": float(p_value),
                "mae": round(float(np.abs(
                    predicted - s2_test["college_draft_order"]).mean()), 2),
                "n_train": int(len(s2_train)),
                "n_test": int(len(s2_test)),
            },
        }
        stage1.get_booster().save_model(
            os.path.join(folds_dir, f"stage1_drafted_{season}.ubj"))
        stage2.get_booster().save_model(
            os.path.join(folds_dir, f"stage2_draft_order_{season}.ubj"))

    # Pooled, over every out-of-fold prediction at once. This is the headline
    # number: it rests on every drafted player in the data rather than one
    # season's worth, which is what the single held-out year used to give.
    pooled_order = oof_order.loc[drafted.index].to_numpy(dtype=float)
    pooled_rho, pooled_p = spearmanr(pooled_order, drafted["college_draft_order"])
    pooled = {
        "stage1": {
            "pr_auc": round(float(average_precision_score(
                eligible["drafted"], oof_probability)), 4),
            "roc_auc": round(float(roc_auc_score(
                eligible["drafted"], oof_probability)), 4),
            "base_rate": round(float(eligible["drafted"].mean()), 4),
            "n": int(len(eligible)),
        },
        "stage2": {
            "spearman": round(float(pooled_rho), 4),
            "p_value": float(pooled_p),
            "mae": round(float(np.abs(
                pooled_order - drafted["college_draft_order"]).mean()), 2),
            "n": int(len(drafted)),
        },
    }

    # The full-data pair, under the default names.
    stage1_full = _fit_stage1(xgb, eligible)
    stage2_full = _fit_stage2(xgb, drafted)
    stage1_full.get_booster().save_model(
        os.path.join(out_dir, "stage1_drafted.ubj"))
    stage2_full.get_booster().save_model(
        os.path.join(out_dir, "stage2_draft_order.ubj"))

    # Hand the out-of-fold columns back so write_matrix can ship them.
    matrix.loc[oof_probability.index, "oof_draft_probability"] = oof_probability
    matrix.loc[oof_order.index, "oof_predicted_order"] = oof_order
    matrix.loc[eligible.index, "oof_fold"] = eligible["year"]

    manifest = {
        "model_version": MODEL_VERSION,
        "lineage": LINEAGE,
        "scored_years": seasons,
        "trained_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "xgboost_version": xgb.__version__,
        "validation": {
            "scheme": "leave-one-season-out",
            "folds": seasons,
            "per_season": per_season,
            "pooled": pooled,
            "note": "Every reported figure is out-of-fold. A season is scored "
                    "only by the model that did not train on it, so the numbers "
                    "here and the board the site draws are the same predictions.",
        },
        "eligibility": {
            # Reported per player-season; it does NOT gate the population any
            # more. See the note above ELIGIBLE_BASES for why.
            "gates_population": False,
            "age": None,
            "age_note": "MLB's other eligibility route is turning 21 near the "
                        "draft. NCAA publishes no date of birth, so that test "
                        "cannot be applied here and is not approximated.",
            "rules": {
                "drafted": "was drafted out of this season -- proof after the "
                           "fact, not a test",
                "class": f"class_ord >= {CLASS_ELIGIBLE_SEASONS}, i.e. Junior "
                         f"or Senior. This is the primary rule and covers "
                         f"31,494 player-seasons.",
                "tenure": f"seasons_elapsed >= {CLASS_ELIGIBLE_SEASONS - 1}, "
                          f"i.e. a third season or later counted from the "
                          f"player's first appearance. Adds 451 rows that "
                          f"class standing alone misses -- sophomores and "
                          f"freshmen who redshirted or transferred in, and so "
                          f"are further through their eligibility than their "
                          f"class year says.",
                "unknown": "neither class nor tenure is known",
                "early-or-ineligible": "an underclassman in their first or "
                                       "second season. Some are genuinely "
                                       "eligible on the age-21 route and "
                                       "cannot be identified as such here.",
            },
            "class_ordinals": {"Fr": 1, "So": 2, "Jr": 3, "Sr": 4, "Gr": 5},
        },
        "stage1": {
            "features": F.model_features(1),
            "params": STAGE1_PARAMS,
            "metrics": pooled["stage1"],
        },
        "stage2": {
            "features": F.model_features(2),
            "params": STAGE2_PARAMS,
            "metrics": pooled["stage2"],
        },
        "stage3": {
            "shipped": False,
            "reason": "A bonus/slot ratio model was attempted and scored a rank "
                      "correlation of 0.003 on held-out data -- indistinguishable "
                      "from noise. Slot values are published facts and are "
                      "available via draft_detail_utils.slot_value().",
        },
        "notes": [
            "Trained on NCAA-published counting statistics and run-value metrics "
            "recomputed from them with college-fitted constants. No third-party "
            "proprietary metric is used, and every input is redistributable.",
            "Stage 1 precision depends on the base rate of the population it is "
            "applied to; see the model card.",
            "The population carries no playing-time minimum, so the base rate "
            "is low and precision figures are not comparable with a model "
            "scored over a qualified leaderboard, where the filter has already "
            "done part of the classifier's work.",
        ],
    }
    with open(os.path.join(out_dir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)
        f.write("\n")

    return manifest


# Columns kept in the shipped matrix: everything a model reads, plus the labels
# and enough identity to trace a row back. The full frame is 16 MB gzipped,
# mostly columns nothing trains on.
_MATRIX_IDENTITY = [
    "player_id", "person_id", "name", "team", "team_id", "division", "year",
    "drafted", "draft_year", "draft_round", "draft_pick", "eligible",
    "eligibility_basis", "class", "role",
]


# Out-of-fold predictions, written back by train(). Shipping them means the
# board for a past season is a lookup rather than a fit, and that the number the
# site prints is provably the one the manifest reports.
_MATRIX_PREDICTIONS = [
    "oof_draft_probability", "oof_predicted_order", "oof_fold",
]


def write_matrix(matrix: pd.DataFrame, out_dir: str) -> str:
    """Persist the training matrix so training is reproducible from the wheel.

    Only draft-eligible rows are kept, since those are the population both
    models are fitted on, and float columns are narrowed to 32-bit. Together
    that is the difference between a 16 MB artifact and one small enough to
    ship.

    Call this *after* :func:`train`, so the out-of-fold columns it adds are
    included.
    """
    os.makedirs(out_dir, exist_ok=True)

    columns = list(dict.fromkeys(
        _MATRIX_IDENTITY + _MATRIX_PREDICTIONS + F.model_features(2)
    ))
    trimmed = matrix.loc[matrix["eligible"], [c for c in columns
                                              if c in matrix.columns]].copy()
    for column in trimmed.select_dtypes(include=["float64"]).columns:
        trimmed[column] = trimmed[column].astype("float32")

    path = os.path.join(out_dir, "training_matrix.csv.gz")
    with gzip.open(path, "wt", newline="", encoding="utf-8") as f:
        trimmed.to_csv(f, index=False, float_format="%.5g")
    return path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", default=data_path("models"))
    parser.add_argument("--matrix-csv", default=None,
                        help="Override the packaged public matrix.")
    parser.add_argument("--matrix", action="store_true",
                        help="Build and save the matrix without training.")
    args = parser.parse_args(argv)

    print("reading the public matrix ...")
    matrix = build_matrix(args.matrix_csv)
    eligible = matrix[matrix["eligible"]]
    print(f"  {len(matrix):6d} player-seasons")
    print(f"  {len(eligible):6d} draft-eligible")
    print(f"  {int(matrix['drafted'].sum()):6d} drafted")
    print(f"  seasons: {sorted(int(y) for y in matrix['year'].unique())}")
    print("  eligibility basis: "
          f"{matrix['eligibility_basis'].value_counts().to_dict()}")

    if args.matrix:
        # No fit, so there are no out-of-fold columns to wait for.
        path = write_matrix(matrix, args.out)
        print(f"  -> {os.path.relpath(path)} "
              f"({os.path.getsize(path) / 1e6:.1f} MB)")
        return 0

    print("\ntraining, leave-one-season-out ...")
    manifest = train(matrix, args.out)
    for season, metrics in sorted(manifest["validation"]["per_season"].items()):
        print(f"  {season}: stage1 pr_auc={metrics['stage1']['pr_auc']:.4f}  "
              f"stage2 spearman={metrics['stage2']['spearman']:.4f} "
              f"(n={metrics['stage2']['n_test']})")
    pooled = manifest["validation"]["pooled"]
    print(f"  pooled: stage1 pr_auc={pooled['stage1']['pr_auc']:.4f}  "
          f"stage2 spearman={pooled['stage2']['spearman']:.4f} "
          f"(n={pooled['stage2']['n']})")

    # After training, so the matrix carries the out-of-fold predictions.
    path = write_matrix(matrix, args.out)
    print(f"\n  -> {os.path.relpath(path)} "
          f"({os.path.getsize(path) / 1e6:.1f} MB)")
    print(f"wrote artifacts -> {os.path.relpath(args.out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

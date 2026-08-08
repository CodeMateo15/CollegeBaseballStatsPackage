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
from ncaa_bbStats._normalize import split_team_league
from ncaa_bbStats._paths import data_path, load_team_stats
from ncaa_bbStats.team_registry import as_team_id, resolve_team

# The held-out season is the most recent one the caches cover, so the reported
# metrics describe the class the board is actually showing, and every earlier
# season is available for training. Holding out 2025 while scoring 2026 cost
# 0.012 PR-AUC on 2026 -- several times seed noise -- because it withheld a
# whole season from a model whose purpose is projecting the newest class.
# Move both when a new season lands.
TRAIN_YEARS = [2021, 2022, 2023, 2024, 2025]
TEST_YEAR = 2026

# Draft eligibility. A player is eligible having completed three college
# seasons, or on turning 21 near the draft.
AGE_ELIGIBLE = 21
CLASS_ELIGIBLE_SEASONS = 3

STAGE1_PARAMS = dict(
    n_estimators=400, learning_rate=0.05, max_depth=6, subsample=0.8,
    colsample_bytree=0.8, random_state=0,
)
STAGE2_PARAMS = dict(
    n_estimators=600, learning_rate=0.03, max_depth=4, subsample=0.8,
    colsample_bytree=0.7, min_child_weight=5, reg_alpha=1.0, reg_lambda=5.0,
    random_state=0,
)

# V7-public: the same three-stage design as the V7 model in the research paper,
# refitted on redistributable inputs. It is a separate lineage, not a revision
# of V7, and the paper's reported metrics do not describe it. See LINEAGE.
MODEL_VERSION = "v7-public-2026.1"

# What differs from the published V7, so a number from one is never quoted for
# the other. Surfaced through model_card().
LINEAGE = {
    "derived_from": "V7 (Biggs & Gerber 2026), three-stage XGBoost",
    "relationship": "separate lineage, not a patched V7",
    "differences": [
        "Features: the nine vendor-proprietary metrics V7 used (wRC+, wOBA, "
        "wRAA, wRC, wSB, Spd, FIP, E-F, LOB%) are replaced by the "
        "package-derived college-calibrated equivalents, so every input is "
        "redistributable.",
        "Stages: two are shipped. V7 also fitted signing-bonus and slot-value "
        "regressors; the bonus/slot ratio scored a rank correlation of 0.003 "
        "on held-out data here, so it is not shipped.",
        "Labels: draft records are matched to careers independently here, from "
        "the public draft feed, rather than reusing V7's matching. The two "
        "disagree on how many college players were drafted (2,466 here against "
        "1,953 in V7's matrix), so the training target is not the same target.",
        "Population: every player-season the public caches cover, 61,279 of "
        "them, against 20,220 in V7's matrix. This model is fitted on a much "
        "larger and less screened population, which is the single biggest "
        "reason the two boards differ.",
        "Hyperparameters and split are this package's, not V7's, so a "
        "V7-to-V7-public comparison reflects features, labels and settings "
        "together rather than any one of them.",
        "Seasons 2021-2026, with 2026 held out of training, so the 2026 "
        "board is an out-of-sample projection and the reported metrics "
        "describe that same class.",
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

def _player_frame(stat_type, suffix):
    from ncaa_bbStats.player_utils import load_player_frame

    df = load_player_frame(stat_type, "noMin")
    keys = ["player_id", "name", "team", "year"]
    stats = [c for c in df.columns if c not in keys + ["team name", "division",
                                                       "age", "qualified"]]
    out = df[keys + ["age"] + stats].copy()
    out = out.rename(columns={c: f"{c}{suffix}" for c in stats})
    return out


def _entity_id_map():
    """Cache player id -> registry career id.

    They differ only for the 76 careers where the vendor issued a second id
    mid-career; `member_ids` records every id a career covers.
    """
    registry = pd.read_csv(data_path("player_registry", "player_registry.csv"))
    mapping = {}
    for entity_id, members in zip(registry["player_id"], registry["member_ids"]):
        for member in str(members).split("|"):
            mapping[member] = entity_id
    return mapping


def _team_frame():
    """One row per (team acronym, season) of NCAA team statistics."""
    rows = []
    for division in (1, 2, 3):
        for season in range(2021, 2027):
            try:
                teams = load_team_stats(season, division)
            except FileNotFoundError:
                continue
            for label, stats in teams.items():
                team_id = resolve_team(split_team_league(label)[0])
                if team_id is None:
                    continue
                row = {f"{k}_team": v for k, v in stats.items()
                       if isinstance(v, (int, float))}
                row["team_id"] = team_id
                row["year"] = season
                rows.append(row)
    df = pd.DataFrame(rows).drop_duplicates(["team_id", "year"])

    runs, allowed = df.get("R (Batting)_team"), df.get("R (Pitching)_team")
    if runs is not None and allowed is not None:
        expected = runs ** 1.83 / (runs ** 1.83 + allowed ** 1.83)
        df["PE_team"] = expected
        df["PE_pct_team"] = expected / df["WPCT_team"].replace(0, np.nan)
    return df


def _rpi_frame():
    from ncaa_bbStats.rpi_utils import _load, available_seasons

    rows = []
    for season in available_seasons():
        for row in _load(season).values():
            rows.append({
                "team_id": row["team_id"], "year": season,
                "rpi_rank_team": row["rpi_rank"],
                "sos_rank_team": row["sos_rank"],
                "nonconference_rpi_rank_team": row["nonconference_rpi_rank"],
                **{
                    f"{prefix}_win_pct_team": row[f"{prefix}_win_pct"]
                    for prefix in ("conference", "overall", "nonconference",
                                   "home", "road", "neutral",
                                   "q1", "q2", "q3", "q4")
                },
                "q1_wins_team": row["q1_wins"],
            })
    return pd.DataFrame(rows)


def _finance_frame():
    from ncaa_bbStats.program_utils import _load

    rows = []
    for (team_id, season), row in _load().items():
        rows.append({
            "team_id": team_id, "year": season,
            **{f"{k}_team": row[k] for k in (
                "budget_pct", "log_budget", "opex_per_player_pct",
                "log_budget_per_player", "roster_size", "log_revenue",
                "net_revenue", "coaching_staff_size", "dept_recruiting_pct",
                "log_dept_coach_salary")},
        })
    return pd.DataFrame(rows)


def _registry_frame():
    path = data_path("player_registry", "player_seasons.csv")
    seasons = pd.read_csv(path)
    registry = pd.read_csv(data_path("player_registry", "player_registry.csv"))
    merged = seasons.merge(
        registry[["player_id", "name", "primary_role", "birth_year_est",
                  "birth_year_source", "mlbam_id", "school_class",
                  "height", "weight", "position", "bats", "throws",
                  "draft_year", "draft_round", "draft_pick"]],
        on="player_id", how="left",
    )
    return merged


def _draft_labels():
    """Drafted-or-not, and where, keyed to registry player ids."""
    registry = pd.read_csv(data_path("player_registry", "player_registry.csv"))
    drafted = registry[registry["draft_year"].notna()].copy()
    return drafted[["player_id", "draft_year", "draft_round", "draft_pick"]]


def build_matrix() -> pd.DataFrame:
    """Assemble one row per eligible player-season, with the draft label."""
    batting = _player_frame("batting", "_bat")
    pitching = _player_frame("pitching", "_pitch")

    # Keyed on the player id, not the name: two players named Cole Conn were
    # team-mates at UIC in 2022 and 2023, and a name join merges their seasons.
    df = batting.merge(pitching, on=["player_id", "year"], how="outer",
                       suffixes=("", "_p"))
    for column in ("name", "team", "age"):
        df[column] = df[column].fillna(df.get(f"{column}_p"))
    df = df.drop(columns=[c for c in df.columns if c.endswith("_p")])

    # Attach career identity, on the career id and season. The previous join was
    # on (year, team) alone, which is one row per team-season on the left and
    # every player on that team on the right -- so birth year, height, weight,
    # position, bats and throws came from an arbitrary team-mate.
    df["player_id"] = df["player_id"].map(_entity_id_map()).fillna(df["player_id"])
    seasons = _registry_frame()
    df = df.merge(
        seasons[["player_id", "year", "primary_role", "birth_year_est",
                 "school_class", "height", "weight", "position", "bats",
                 "throws"]].drop_duplicates(["player_id", "year"]),
        on=["player_id", "year"], how="left", suffixes=("", "_reg"),
    )

    df["role"] = df["primary_role"].map(F.ROLE_MAP)

    # Team context.
    df["team_id"] = df["team"].map(lambda t: as_team_id(str(t)))
    for frame in (_team_frame(), _rpi_frame(), _finance_frame()):
        if not frame.empty:
            df = df.merge(frame, on=["team_id", "year"], how="left")

    F.add_usage_features(df)

    # Draft label. A college season leads to the draft that summer or the next.
    labels = _draft_labels().set_index("player_id")
    df["draft_year"] = df["player_id"].map(labels["draft_year"])
    df["draft_pick"] = df["player_id"].map(labels["draft_pick"])
    df["draft_round"] = df["player_id"].map(labels["draft_round"])
    df["drafted"] = (
        df["draft_year"].notna() & (df["draft_year"] == df["year"])
    ).astype(int)

    # Eligibility. Seasons completed as of this row's year, not career total --
    # otherwise a freshman season counts as eligible because the player later
    # played three.
    seasons_by_player = (
        seasons.groupby("player_id")["year"].apply(list).to_dict()
    )
    df["seasons_to_date"] = [
        sum(1 for y in seasons_by_player.get(pid, []) if y <= year)
        for pid, year in zip(df["player_id"], df["year"])
    ]
    df["age_filled"] = df["age"].fillna(df["year"] - df["birth_year_est"])
    df["eligibility_basis"] = [
        _eligibility_basis(drafted, seasons, age)
        for drafted, seasons, age in zip(
            df["drafted"], df["seasons_to_date"], df["age_filled"]
        )
    ]
    df["eligible"] = df["eligibility_basis"].isin(["drafted", "class", "age"])

    # Biography, known only for drafted players -- Stage 2 only.
    df["api_height"] = df["height"].map(_height_to_inches)
    df["api_weight"] = pd.to_numeric(df["weight"], errors="coerce")
    df["api_position"] = df["position"].astype("category").cat.codes
    df["api_bats"] = df["bats"].map({"R": 0, "L": 1, "S": 2})
    df["api_throws"] = df["throws"].map({"R": 0, "L": 1, "S": 2})

    return df


def _eligibility_basis(drafted, seasons_to_date, age):
    """Why a player-season is or is not draft eligible.

    Ordered strongest evidence first. ``drafted`` must come first so the filter
    can never delete a positive label.
    """
    if drafted:
        return "drafted"
    if seasons_to_date >= CLASS_ELIGIBLE_SEASONS:
        return "class"
    if pd.notna(age) and age >= AGE_ELIGIBLE:
        return "age"
    if pd.isna(age):
        return "unknown"
    return "ineligible"


def _height_to_inches(value):
    if not isinstance(value, str) or "'" not in value:
        return np.nan
    try:
        feet, inches = value.replace('"', "").split("'")
        return int(feet.strip()) * 12 + int(inches.strip() or 0)
    except (ValueError, IndexError):
        return np.nan


# --- training ------------------------------------------------------------

def train(matrix: pd.DataFrame, out_dir: str, *, test_year: int = TEST_YEAR):
    """Fit both stages and write the artifacts. Returns the manifest."""
    xgb = _require_xgboost()
    from sklearn.metrics import average_precision_score, roc_auc_score
    from scipy.stats import spearmanr

    os.makedirs(out_dir, exist_ok=True)
    eligible = matrix[matrix["eligible"]].copy()

    # Stage 1
    s1_features = F.model_features(1)
    train_rows = eligible[eligible["year"] < test_year]
    test_rows = eligible[eligible["year"] == test_year]

    x_train = F.align(train_rows, s1_features).astype(float)
    x_test = F.align(test_rows, s1_features).astype(float)
    y_train, y_test = train_rows["drafted"], test_rows["drafted"]

    stage1 = xgb.XGBClassifier(**STAGE1_PARAMS)
    stage1.fit(x_train, y_train)
    probabilities = stage1.predict_proba(x_test)[:, 1]

    stage1_metrics = {
        "pr_auc": round(float(average_precision_score(y_test, probabilities)), 4),
        "roc_auc": round(float(roc_auc_score(y_test, probabilities)), 4),
        "base_rate": round(float(y_test.mean()), 4),
        "n_train": int(len(x_train)),
        "n_test": int(len(x_test)),
    }
    stage1.get_booster().save_model(os.path.join(out_dir, "stage1_drafted.ubj"))

    # Stage 2: order within the drafted college class.
    s2_features = F.model_features(2)
    drafted = eligible[eligible["drafted"] == 1].copy()
    drafted = drafted.sort_values(["year", "draft_pick"])
    drafted["college_draft_order"] = drafted.groupby("year").cumcount() + 1

    d_train = drafted[drafted["year"] < test_year]
    d_test = drafted[drafted["year"] == test_year]

    stage2 = xgb.XGBRegressor(**STAGE2_PARAMS, eval_metric="mae")
    stage2.fit(
        F.align(d_train, s2_features).astype(float),
        d_train["college_draft_order"],
    )
    predicted = stage2.predict(F.align(d_test, s2_features).astype(float))
    rho, p_value = spearmanr(predicted, d_test["college_draft_order"])

    stage2_metrics = {
        "spearman": round(float(rho), 4),
        "p_value": float(p_value),
        "mae": round(float(np.abs(predicted - d_test["college_draft_order"]).mean()), 2),
        "n_train": int(len(d_train)),
        "n_test": int(len(d_test)),
    }
    stage2.get_booster().save_model(os.path.join(out_dir, "stage2_draft_order.ubj"))

    manifest = {
        "model_version": MODEL_VERSION,
        "lineage": LINEAGE,
        "scored_years": sorted(int(y) for y in matrix["year"].unique()),
        "trained_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "xgboost_version": xgb.__version__,
        "train_years": sorted(int(y) for y in train_rows["year"].unique()),
        "test_year": test_year,
        "eligibility": {
            "age": AGE_ELIGIBLE,
            "seasons": CLASS_ELIGIBLE_SEASONS,
            "unknown_treated_as_eligible": False,
        },
        "stage1": {
            "features": s1_features,
            "params": STAGE1_PARAMS,
            "metrics": stage1_metrics,
        },
        "stage2": {
            "features": s2_features,
            "params": STAGE2_PARAMS,
            "metrics": stage2_metrics,
        },
        "stage3": {
            "shipped": False,
            "reason": "A bonus/slot ratio model was attempted and scored a rank "
                      "correlation of 0.003 on held-out data -- indistinguishable "
                      "from noise. Slot values are published facts and are "
                      "available via draft_detail_utils.slot_value().",
        },
        "notes": [
            "Trained on public NCAA counting statistics and package-derived "
            "run-value metrics. No third-party proprietary metric is used.",
            "Stage 1 precision depends on the base rate of the population it is "
            "applied to; see the model card.",
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
    "player_id", "name", "team", "team_id", "year", "drafted", "draft_year",
    "draft_round", "draft_pick", "eligible", "eligibility_basis",
    "seasons_to_date", "age_filled", "primary_role",
]


def write_matrix(matrix: pd.DataFrame, out_dir: str) -> str:
    """Persist the training matrix so training is reproducible from the wheel.

    Only draft-eligible rows are kept, since those are the population both
    models are fitted on, and float columns are narrowed to 32-bit. Together
    that is the difference between a 16 MB artifact and one small enough to
    ship.
    """
    os.makedirs(out_dir, exist_ok=True)

    columns = list(dict.fromkeys(
        _MATRIX_IDENTITY + F.model_features(2)
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
    parser.add_argument("--test-year", type=int, default=TEST_YEAR)
    parser.add_argument("--matrix", action="store_true",
                        help="Build and save the matrix without training.")
    args = parser.parse_args(argv)

    print("building training matrix ...")
    matrix = build_matrix()
    eligible = matrix[matrix["eligible"]]
    print(f"  {len(matrix):6d} player-seasons")
    print(f"  {len(eligible):6d} draft-eligible")
    print(f"  {int(matrix['drafted'].sum()):6d} drafted")
    print("  eligibility basis: "
          f"{matrix['eligibility_basis'].value_counts().to_dict()}")

    path = write_matrix(matrix, args.out)
    print(f"  -> {os.path.relpath(path)} "
          f"({os.path.getsize(path) / 1e6:.1f} MB)")

    if args.matrix:
        return 0

    print("\ntraining ...")
    manifest = train(matrix, args.out, test_year=args.test_year)
    print(f"  stage 1: {manifest['stage1']['metrics']}")
    print(f"  stage 2: {manifest['stage2']['metrics']}")
    print(f"\nwrote artifacts -> {os.path.relpath(args.out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

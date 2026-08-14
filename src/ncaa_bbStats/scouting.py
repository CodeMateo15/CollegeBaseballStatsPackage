"""Draft predictions, explanations, and scouting reports.

    >>> from ncaa_bbStats import scouting_report
    >>> print(scouting_report("Kade Anderson", 2025))

Two models back this: a classifier for whether a player-season leads to being
drafted, and a regressor for where a drafted player falls within their college
class. Both are trained only on public NCAA statistics and the package's own
derived metrics -- see :func:`model_card` for the held-out numbers and the
limitations.

Needs the ``model`` extra for predictions (``pip install
"ncaa_bbStats[model]"``), and the ``explain`` extra for SHAP attributions.
Without SHAP, explanations fall back to gain-weighted deviation from the median
and report which method was used.
"""

import json
import math
import os
from functools import lru_cache
from typing import Literal, Optional

import numpy as np
import pandas as pd

from ncaa_bbStats import features as F
from ncaa_bbStats._paths import data_path

__all__ = [
    "predict_draft_probability",
    "predict_draft_order",
    "draft_board",
    "scouting_report",
    "explain_prediction",
    "feature_contributions",
    "predict_from_stats",
    "is_draft_eligible",
    "model_card",
    "MissingDependencyError",
]

#: Below this predicted probability, draft-position output is suppressed. The
#: order model is trained only on players who were actually drafted, so applying
#: it to a long-shot is extrapolation dressed up as a number.
MIN_PROBABILITY_FOR_ORDER = 0.25

_GRADE_BANDS = [
    (90, "A+"), (80, "A"), (70, "A-"), (60, "B+"), (50, "B"), (40, "B-"),
    (30, "C+"), (20, "C"), (10, "C-"), (5, "D+"), (2, "D"), (1, "D-"),
]

_NARRATIVE = {
    "A+": "a top-of-the-draft profile", "A": "a strong draft profile",
    "A-": "a solid draft profile", "B+": "a likely selection",
    "B": "a coin-flip profile", "B-": "a fringe profile",
    "C+": "a long shot", "C": "a long shot",
    "C-": "an unlikely selection", "D+": "an unlikely selection",
    "D": "a clearly undrafted-leaning profile",
    "D-": "a clearly undrafted-leaning profile",
    "F": "a clearly undrafted-leaning profile",
}


class MissingDependencyError(ImportError):
    """Raised when an optional extra is needed but not installed."""


def _require(module_name: str, extra: str):
    try:
        return __import__(module_name)
    except ImportError as exc:
        raise MissingDependencyError(
            f"This needs {module_name}. Install it with:\n"
            f'    pip install "ncaa_bbStats[{extra}]"'
        ) from exc


@lru_cache(maxsize=1)
def _manifest() -> dict:
    path = data_path("models", "manifest.json")
    if not os.path.isfile(path):
        raise FileNotFoundError(
            f"No trained models found at {path}. "
            "Run `python -m ncaa_bbStats.model_store`."
        )
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=2)
def _model(stage: int):
    """Load a booster, verifying its feature contract."""
    xgb = _require("xgboost", "model")
    manifest = _manifest()
    key = f"stage{stage}"
    filename = {1: "stage1_drafted.ubj", 2: "stage2_draft_order.ubj"}[stage]

    expected = manifest[key]["features"]
    current = F.model_features(stage)
    if expected != current:
        # A permuted feature vector still produces numbers, just confidently
        # wrong ones. Fail instead.
        raise RuntimeError(
            f"Stage {stage} feature mismatch: the shipped model expects "
            f"{len(expected)} features in a specific order, but "
            f"features.model_features({stage}) returns {len(current)}. "
            "Retrain with `python -m ncaa_bbStats.model_store`."
        )

    booster = xgb.Booster()
    booster.load_model(data_path("models", filename))
    return booster


@lru_cache(maxsize=1)
def _matrix() -> pd.DataFrame:
    """The shipped training matrix, which is also the lookup table."""
    path = data_path("models", "training_matrix.csv.gz")
    if not os.path.isfile(path):
        raise FileNotFoundError(
            f"No training matrix at {path}. "
            "Run `python -m ncaa_bbStats.model_store --matrix`."
        )
    return pd.read_csv(path, low_memory=False)


def _find_rows(name: str, season: Optional[int] = None) -> pd.DataFrame:
    matrix = _matrix()
    rows = matrix[matrix["name"].str.lower() == name.lower()]
    if season is not None:
        rows = rows[rows["year"] == season]
    return rows.sort_values("year")


def _predict(stage: int, frame: pd.DataFrame) -> np.ndarray:
    xgb = _require("xgboost", "model")
    aligned = F.align(frame, F.model_features(stage))
    matrix = xgb.DMatrix(aligned, feature_names=list(aligned.columns))
    predicted = _model(stage).predict(matrix)
    if stage == 2:
        # The regressor is unbounded, so a player well clear of the field
        # extrapolates past the top of the board -- the reference implementation
        # reports "~pick -2" for its best prospect. There is no zeroth pick;
        # floor it at 1.
        predicted = np.clip(predicted, 1.0, None)
    return predicted


def predict_draft_probability(name: str, season: Optional[int] = None) -> Optional[float]:
    """Modelled probability that a player-season leads to being drafted.

    Args:
        name (str): Player name, matched case-insensitively.
        season (int, optional): One season. Defaults to their most recent.

    Returns:
        float | None: Probability in [0, 1], or None if the player is not in the
        eligible population.
    """
    rows = _find_rows(name, season)
    if rows.empty:
        return None
    return float(_predict(1, rows.tail(1))[0])


def predict_draft_order(name: str, season: Optional[int] = None) -> Optional[float]:
    """Modelled position within the college portion of a draft class.

    Lower is better: 1 would be the first college player selected.

    Args:
        name (str): Player name, matched case-insensitively.
        season (int, optional): One season. Defaults to their most recent.

    Returns:
        float | None: Predicted order, or None if the player is not found.
    """
    rows = _find_rows(name, season)
    if rows.empty:
        return None
    return float(_predict(2, rows.tail(1))[0])


def is_draft_eligible(name: str, season: Optional[int] = None):
    """Whether a player was draft eligible, and on what basis.

    Eligibility is **inferred**, not looked up: from seasons completed and from
    age, which is itself estimated for most players. The basis string says which
    evidence was used, so a caller can decide how much to trust it.

    Args:
        name (str): Player name, matched case-insensitively.
        season (int, optional): One season. Defaults to their most recent.

    Returns:
        tuple[bool, str] | None: ``(eligible, basis)`` where basis is one of
        ``"drafted"``, ``"class"``, ``"age"``, ``"unknown"``, ``"ineligible"``.
        None if the player is not in the data.
    """
    rows = _find_rows(name, season)
    if rows.empty:
        return None
    row = rows.iloc[-1]
    return bool(row["eligible"]), str(row["eligibility_basis"])


def _grade(probability: float) -> str:
    percent = probability * 100
    for threshold, letter in _GRADE_BANDS:
        if percent >= threshold:
            return letter
    return "F"


def _label(feature: str) -> str:
    """Human-readable feature name."""
    text = feature
    for suffix, tag in (("_pitch", " (pitching)"), ("_bat", " (batting)"),
                        ("_team", " (team)")):
        if text.endswith(suffix):
            text = text[: -len(suffix)] + tag
            break
    return text.replace("_", " ")


def explain_prediction(
    name: str,
    season: Optional[int] = None,
    *,
    top_n: int = 5,
    method: Literal["auto", "shap", "gain"] = "auto",
) -> Optional[dict]:
    """Which inputs pushed a player's draft probability up or down.

    Args:
        name (str): Player name, matched case-insensitively.
        season (int, optional): One season. Defaults to their most recent.
        top_n (int): How many strengths and concerns to return.
        method (str): ``"shap"`` for exact attributions, ``"gain"`` for the
            dependency-free fallback, ``"auto"`` to use SHAP when available.

    Returns:
        dict | None: ``method``, ``draft_probability``, ``strengths``,
        ``concerns``. Each entry has ``feature``, ``label``, ``value``,
        ``median``, and ``impact`` in percentage points of probability. None if
        the player is not found.
    """
    rows = _find_rows(name, season)
    if rows.empty:
        return None
    row = rows.tail(1)

    features = F.model_features(1)
    aligned = F.align(row, features)
    probability = float(_predict(1, row)[0])
    medians = F.align(_matrix(), features).median(numeric_only=True)

    contributions, used = None, "gain"
    if method in ("auto", "shap"):
        try:
            explainer = _explainer(1)
            values = explainer.shap_values(aligned)
            if isinstance(values, list):
                values = values[1]
            contributions = np.asarray(values)[0]
            base = explainer.expected_value
            base = float(np.asarray(base).ravel()[-1])
            used = "shap"
        except MissingDependencyError:
            if method == "shap":
                raise
        except Exception:
            contributions = None

    records = []
    if contributions is not None:
        # SHAP values are in log-odds. Convert each to the probability it
        # actually moved, by removing that one contribution and re-expiting --
        # a naive expit(shap) would be meaningless on its own scale.
        total = base + float(np.nansum(contributions))
        for i, feature in enumerate(features):
            value = aligned.iloc[0, i]
            if pd.isna(value):
                continue
            impact = (_expit(total) - _expit(total - contributions[i])) * 100
            records.append((feature, float(value), impact))
    else:
        gains = _model(1).get_score(importance_type="gain")
        total_gain = sum(gains.values()) or 1.0
        stds = F.align(_matrix(), features).std(numeric_only=True)
        for feature in features:
            value = aligned.iloc[0][feature]
            std = stds.get(feature)
            if pd.isna(value) or not std:
                continue
            z = (value - medians.get(feature, 0)) / std
            records.append((
                feature, float(value),
                gains.get(feature, 0.0) / total_gain * float(z) * 100,
            ))

    records.sort(key=lambda r: -r[2])
    strengths = [r for r in records if r[2] > 0][:top_n]
    concerns = [r for r in reversed(records) if r[2] < 0][:top_n]

    def pack(items):
        return [
            {
                "feature": feature,
                "label": _label(feature),
                "value": round(value, 4),
                "median": round(float(medians.get(feature, float("nan"))), 4),
                "impact": round(impact, 4),
            }
            for feature, value, impact in items
        ]

    return {
        "method": used,
        "draft_probability": probability,
        "strengths": pack(strengths),
        "concerns": pack(concerns),
    }


def _expit(x):
    return 1.0 / (1.0 + math.exp(-x)) if -700 < x < 700 else float(x > 0)


@lru_cache(maxsize=2)
def _explainer(stage: int):
    """One TreeExplainer per stage.

    Building it costs an order of magnitude more than explaining a row, so it is
    kept rather than rebuilt per call.
    """
    shap = _require("shap", "explain")
    return shap.TreeExplainer(_model(stage))


def feature_contributions(
    name: Optional[str] = None,
    season: Optional[int] = None,
    *,
    stage: Literal[1, 2] = 1,
    features: Optional[object] = None,
) -> Optional[dict]:
    """Exact SHAP contributions for one prediction, in the model's own units.

    Where :func:`explain_prediction` returns a readable shortlist in percentage
    points, this returns every feature's raw contribution together with the base
    value, so that ``base + sum(contributions) == prediction`` holds exactly.
    That is what a waterfall chart needs; a shortlist of re-expited
    leave-one-out impacts cannot be stacked.

    Stage 1 is a binary classifier, so ``base``, the contributions and
    ``prediction`` are all log-odds -- apply a logistic to read a probability.
    Stage 2 is a squared-error regressor, so they are already in college draft
    order units and no link function is involved.

    Features the caller never supplied are kept, with a ``value`` of None. A
    missing input still has a contribution: the models route missing values down
    a learned default branch, so absence is itself a signal, and dropping those
    entries would break the sum this function exists to guarantee.

    Needs SHAP (``pip install "ncaa_bbStats[explain]"``). There is no gain-based
    fallback: gain has no base value and does not sum to the prediction, so it
    cannot answer this question at all.

    Args:
        name (str, optional): Player name, matched case-insensitively. Ignored
            when ``features`` is given.
        season (int, optional): One season. Defaults to their most recent.
        stage (int): 1 for the drafted/not-drafted classifier, 2 for the
            draft-order regressor.
        features (pandas.DataFrame | pandas.Series | dict, optional): A single
            feature row to explain instead of a stored player -- for example the
            ``feature_row`` returned by :func:`predict_from_stats`. That row is
            built over the Stage 2 column set, which is a superset of Stage 1's,
            so the same row explains either stage.

    Returns:
        dict | None: ``stage``, ``units`` (``"log-odds"`` or ``"draft order"``),
        ``base``, ``prediction``, and ``contributions`` -- one entry per model
        feature, each with ``feature``, ``label``, ``value`` (None when the
        input was missing) and ``contribution``, sorted by descending absolute
        contribution. ``prediction`` is the model's raw output, which for Stage 2
        is *before* the floor at 1 that :func:`predict_draft_order` applies.
        None if the player is not found.

    Raises:
        MissingDependencyError: if SHAP is not installed.
    """
    if features is not None:
        if isinstance(features, pd.DataFrame):
            row = features.head(1)
        elif isinstance(features, pd.Series):
            row = features.to_frame().T
        else:
            row = pd.DataFrame([features])
    else:
        rows = _find_rows(name, season)
        if rows.empty:
            return None
        row = rows.tail(1)

    names = F.model_features(stage)
    aligned = F.align(row, names)

    explainer = _explainer(stage)
    values = explainer.shap_values(aligned)
    if isinstance(values, list):
        values = values[1]
    # float64 before anything is added up. SHAP hands back the booster's float32,
    # and accumulating 150 of those toward a Stage 2 total near 200 loses enough
    # precision to visibly miss the prediction the bars are supposed to reach.
    contributions = np.asarray(values, dtype=np.float64)[0]
    base = float(np.asarray(explainer.expected_value).ravel()[-1])

    # The sum is the answer, not a check on it. Deriving the total from
    # _predict() instead would disagree with the bars for the handful of Stage 2
    # rows whose raw output falls below the floor that _predict applies.
    prediction = base + float(contributions.sum())

    records = []
    for i, feature in enumerate(names):
        value = aligned.iloc[0, i]
        records.append({
            "feature": feature,
            "label": _label(feature),
            "value": None if pd.isna(value) else round(float(value), 4),
            # Deliberately unrounded: rounding 150 of these to four places
            # drifts the total by enough to see on the Stage 2 axis.
            "contribution": float(contributions[i]),
        })
    records.sort(key=lambda r: -abs(r["contribution"]))

    return {
        "stage": int(stage),
        "units": "log-odds" if stage == 1 else "draft order",
        "base": base,
        "prediction": prediction,
        "contributions": records,
    }


def scouting_report(
    name: str, season: Optional[int] = None, *, top_n: int = 5
) -> Optional[str]:
    """A readable scouting report for a player.

    Args:
        name (str): Player name, matched case-insensitively.
        season (int, optional): One season. Defaults to their most recent.
        top_n (int): How many strengths and concerns to list.

    Returns:
        str | None: The formatted report, or None if the player is not found.
    """
    rows = _find_rows(name, season)
    if rows.empty:
        return None

    row = rows.iloc[-1]
    year = int(row["year"])
    probability = float(_predict(1, rows.tail(1))[0])
    grade = _grade(probability)
    explanation = explain_prediction(name, year, top_n=top_n) or {}

    from ncaa_bbStats.team_registry import team_info

    info = team_info(str(row.get("team_id") or ""), season=year) or {}
    role = str(row.get("primary_role") or "player").replace("_", "-")

    lines = [
        "=" * 66,
        f"  {row['name']}  |  {year}  |  {role}",
    ]
    if info:
        lines.append(
            f"  {info.get('canonical_name')}"
            f"  ({info.get('conference') or 'unknown conference'})"
        )
    lines += [
        "=" * 66,
        f"  Draft grade: {grade}   (modelled probability {probability:.1%})",
    ]

    order = float(_predict(2, rows.tail(1))[0])
    if probability >= MIN_PROBABILITY_FOR_ORDER:
        lines.append(f"  Projected college draft order: ~{order:.0f}")
    else:
        lines.append(
            f"  Draft order suppressed: probability {probability:.1%} is below "
            f"{MIN_PROBABILITY_FOR_ORDER:.0%}."
        )
        lines.append(
            "  The order model is trained only on drafted players, so applying "
            "it here would be extrapolation."
        )

    eligible = is_draft_eligible(name, year)
    if eligible:
        lines.append(f"  Draft eligible: {eligible[0]} (basis: {eligible[1]})")

    if pd.notna(row.get("draft_pick")):
        lines.append(
            f"  Actual: selected #{int(row['draft_pick'])} "
            f"in round {row.get('draft_round')}"
        )

    take = _NARRATIVE.get(grade, "an unclear profile")
    strengths = explanation.get("strengths") or []
    concerns = explanation.get("concerns") or []
    lines += ["-" * 66, f"  Take: the model sees {take}."]
    if strengths:
        lines[-1] += f" Driven by {strengths[0]['label']}."
    if concerns:
        lines.append(f"  Main concern: {concerns[0]['label']}.")

    def block(title, items, sign):
        out = ["", f"  {title}"]
        if not items:
            out.append("    (none)")
            return out
        out.append(f"    {'feature':<28}{'value':>12}{'median':>12}{'impact':>10}")
        for item in items:
            out.append(
                f"    {sign} {item['label'][:26]:<26}"
                f"{item['value']:>12.3f}{item['median']:>12.3f}"
                f"{item['impact']:>9.2f}%"
            )
        return out

    lines += block(f"Top {top_n} strengths", strengths, "^")
    lines += block(f"Top {top_n} concerns", concerns, "v")
    lines += [
        "",
        f"  Explanations by {explanation.get('method', 'gain')}; impact is in "
        "percentage points",
        "  of draft probability. See model_card() for held-out performance.",
        "=" * 66,
    ]
    return "\n".join(lines)


def _stat_line_frame(role, age, stats, team, season):
    """Build the one-row feature frame a typed-in stat line scores against.

    Split out so that the row which produced a prediction is the same row an
    explanation is computed from -- rebuilding it a second time is how the two
    quietly come to disagree.

    Returns:
        tuple: ``(frame, supplied, imputed, season)``. The frame carries the
        Stage 2 column set, a superset of Stage 1's, with usage features derived.
    """
    matrix = _matrix()
    if season is None:
        season = int(matrix["year"].max())

    features = F.model_features(2)
    row = pd.Series(index=features, dtype="float64")
    row["age"] = age
    row["role"] = F.ROLE_MAP.get(role, 0)

    supplied = set()
    for key, value in stats.items():
        if key in row.index:
            row[key] = value
            supplied.add(key)
        elif f"{key}_bat" in row.index and role != "pitcher":
            row[f"{key}_bat"] = value
            supplied.add(f"{key}_bat")
        elif f"{key}_pitch" in row.index and role != "batter":
            row[f"{key}_pitch"] = value
            supplied.add(f"{key}_pitch")

    team_columns = [f for f in features if f.endswith("_team")]
    context = None
    if team is not None:
        from ncaa_bbStats.team_registry import as_team_id

        team_id = as_team_id(team)
        match = matrix[(matrix["team_id"] == team_id) & (matrix["year"] == season)]
        if not match.empty:
            context = match.iloc[0]

    season_rows = matrix[matrix["year"] == season]
    medians = (season_rows if not season_rows.empty else matrix).median(
        numeric_only=True
    )
    imputed = []
    for column in team_columns:
        if pd.isna(row[column]):
            if context is not None and pd.notna(context.get(column)):
                row[column] = context[column]
            elif column in medians:
                row[column] = medians[column]
                imputed.append(column)

    frame = pd.DataFrame([row])
    F.add_usage_features(frame)
    return frame, supplied, imputed, season


def predict_from_stats(
    role: Literal["batter", "pitcher", "two_way"],
    age: float,
    stats: dict,
    *,
    team: Optional[str] = None,
    season: Optional[int] = None,
    name: str = "Custom player",
) -> dict:
    """Score a stat line that is not in the data.

    Supply as much or as little as you have. Team context is filled from the
    named program, or from the season median if no team is given; unspecified
    player statistics are left missing, which the models handle natively.

    Args:
        role (str): ``"batter"``, ``"pitcher"``, or ``"two_way"``.
        age (float): Player age during the season.
        stats (dict): Any subset of the feature names, e.g.
            ``{"era_pitch": 2.80, "so_pitch": 120, "ip_pitch": 95.0}``.
        team (str, optional): Any spelling of a team name, for context.
        season (int, optional): Season to take team context and league constants
            from. Defaults to the most recent season in the data, so it follows
            the cache forward instead of pinning to whichever year was current
            when this was written.
        name (str): Label used in the returned report.

    Returns:
        dict: ``draft_probability``, ``draft_grade``, ``predicted_order``
        (None when suppressed), ``imputed_features``, ``confidence``,
        ``report``, and ``feature_row`` -- the row that was actually scored, as
        a plain dict with None for anything left missing. Pass it to
        :func:`feature_contributions` to explain this same prediction.
    """
    frame, supplied, imputed, season = _stat_line_frame(
        role, age, stats, team, season
    )
    features = F.model_features(2)

    probability = float(_predict(1, frame)[0])
    order = float(_predict(2, frame)[0])
    grade = _grade(probability)

    player_features = [
        f for f in features
        if f.endswith(("_bat", "_pitch")) or f in ("age", "role")
    ]
    missing = [f for f in player_features if f not in supplied and f not in ("age", "role")]
    missing_share = len(missing) / max(1, len(player_features))
    confidence = (
        "low" if missing_share > 0.7
        else "medium" if missing_share > 0.4
        else "high"
    )

    lines = [
        "=" * 66,
        f"  {name}  |  {role}, age {age:g}  |  {season} context"
        + (f"  ({team})" if team else "  (league median)"),
        "=" * 66,
        f"  Draft grade: {grade}   (modelled probability {probability:.1%})",
    ]
    if probability >= MIN_PROBABILITY_FOR_ORDER:
        lines.append(f"  Projected college draft order: ~{order:.0f}")
    else:
        lines.append(
            f"  Draft order suppressed: probability {probability:.1%} is below "
            f"{MIN_PROBABILITY_FOR_ORDER:.0%}."
        )
    lines += [
        "-" * 66,
        f"  Supplied {len(supplied)} statistics; {len(missing)} left unset "
        f"({missing_share:.0%}).",
        f"  Confidence: {confidence}.",
    ]
    if imputed:
        lines.append(
            f"  Team context imputed from the {season} median "
            f"({len(imputed)} fields)."
        )
    lines.append("=" * 66)

    return {
        "name": name,
        "role": role,
        "draft_probability": probability,
        "draft_grade": grade,
        "predicted_order": (
            order if probability >= MIN_PROBABILITY_FOR_ORDER else None
        ),
        "supplied_features": sorted(supplied),
        "imputed_features": imputed,
        "confidence": confidence,
        "report": "\n".join(lines),
        # A plain dict rather than the frame: the rest of this return value is
        # printable and serialisable, and F.align turns None back into NaN.
        "feature_row": {
            column: (None if pd.isna(value) else float(value))
            for column, value in frame.iloc[0].items()
        },
    }


def draft_board(
    season: int, *, n: int = 100, min_probability: float = 0.0
) -> list[dict]:
    """Rank a season's eligible players by modelled draft probability.

    Args:
        season (int): Season year.
        n (int): How many players to return.
        min_probability (float): Drop players below this probability.

    Returns:
        list[dict]: ``rank``, ``name``, ``team``, ``draft_probability``,
        ``draft_grade``, ``predicted_order``, ``actual_pick``.
    """
    rows = _matrix()[_matrix()["year"] == season]
    if rows.empty:
        return []

    probabilities = _predict(1, rows)
    orders = _predict(2, rows)

    board = []
    for (_, row), probability, order in zip(rows.iterrows(), probabilities, orders):
        if probability < min_probability:
            continue
        board.append({
            "name": row["name"],
            "team": row["team"],
            "draft_probability": round(float(probability), 4),
            "draft_grade": _grade(float(probability)),
            "predicted_order": (
                round(float(order), 1)
                if probability >= MIN_PROBABILITY_FOR_ORDER else None
            ),
            "actual_pick": (
                int(row["draft_pick"]) if pd.notna(row.get("draft_pick")) else None
            ),
        })

    board.sort(key=lambda r: -r["draft_probability"])
    for rank, entry in enumerate(board[:n], start=1):
        entry["rank"] = rank
    return board[:n]


def model_card(stage: Optional[int] = None) -> dict:
    """Provenance, held-out performance, and limitations of the shipped models.

    Published as a function rather than a documentation footnote, so the numbers
    travel with the predictions.

    Args:
        stage (int, optional): Restrict to one stage.

    Returns:
        dict: The manifest, plus a ``limitations`` list and the reference
        implementation's numbers for comparison.
    """
    manifest = dict(_manifest())
    manifest["limitations"] = [
        "Stage 1 precision depends on the base rate of the population it is "
        "applied to. On the held-out season roughly 7% of eligible players were "
        "drafted; applied to a pre-screened shortlist, precision is higher, and "
        "applied to every player in the country, lower.",
        "Draft eligibility is inferred from seasons completed and from age, and "
        "age is itself estimated for most players. is_draft_eligible() returns "
        "the basis so the inference is visible.",
        "The order model is trained only on players who were drafted. Applying "
        "it below a 25% draft probability is extrapolation, and it is "
        "suppressed there.",
        "No third stage. A bonus/slot ratio model scored a rank correlation of "
        "0.003 on held-out data and is not shipped; slot values are published "
        "facts, available via draft_detail_utils.slot_value().",
        "Trained on 2021-2025 and tested on 2026, a single held-out season. "
        "These are not cross-validated estimates, and one season is a small "
        "sample: 2026 scores lower than 2025 did, which is a property of the "
        "class as much as of the model.",
    ]
    manifest["reference_implementation"] = {
        "name": "V7 (Biggs & Gerber 2026)",
        "note": "V7 is the published research model this one derives from. It "
                "used proprietary third-party metrics as features, a different "
                "label set and population, its own hyperparameters, and a 2026 "
                "test year. The numbers below are for orientation only. They "
                "are NOT this model's performance, and because features, "
                "labels, population and settings all differ, the gap between "
                "the two cannot be attributed to any one of them. See "
                "model_card()['lineage'].",
        "stage1_pr_auc": 0.725,
        "stage1_roc_auc": 0.949,
        "stage2_spearman": 0.653,
    }
    if stage is not None:
        key = f"stage{stage}"
        return {
            "model_version": manifest["model_version"],
            key: manifest[key],
            "limitations": manifest["limitations"],
        }
    return manifest

Scouting and Draft Prediction
=============================

Draft probabilities, explanations, and scouting reports.

.. code-block:: python

    >>> from ncaa_bbStats import scouting_report
    >>> print(scouting_report("Kade Anderson", 2025))
    ==================================================================
      Kade Anderson  |  2025  |  pitcher
      LSU  (SEC)
    ==================================================================
      Draft grade: A+   (modelled probability 98.5%)
      Projected college draft order: ~1
      Draft eligible: True (basis: drafted)
      Actual: selected #3 in round 1
    ------------------------------------------------------------------
      Take: the model sees a top-of-the-draft profile. Driven by age.
      Main concern: BB (Batting) (team).

      Top 5 strengths
        feature                            value      median    impact
        ^ age                             20.000      22.000     5.92%
        ^ so (pitching)                  180.000      22.000     5.12%
        ^ k% (pitching)                    0.374       0.189     1.04%
        ...

Overview
--------

Two models ship:

- **Stage 1** classifies whether a player-season leads to being drafted.
- **Stage 2** orders drafted players within their college class.

A third stage predicting signing bonus as a share of slot value was attempted
and is **not shipped**: it scored a rank correlation of 0.003 on held-out data,
which is noise with a ``.predict()`` method. Slot values are published facts and
are available directly as :func:`slot_value`.

Read :func:`model_card` before quoting any of these numbers.

Installation
------------

Predictions need XGBoost; explanations optionally use SHAP::

    pip install "ncaa_bbStats[model]"      # predictions
    pip install "ncaa_bbStats[explain]"    # predictions + SHAP attributions

Without SHAP, :func:`explain_prediction` falls back to gain-weighted deviation
from the median and reports ``method="gain"`` so you know which you got.
Importing ``ncaa_bbStats`` never loads XGBoost.

Functions
---------

.. py:function:: predict_draft_probability(name: str, season: int | None = None) -> float | None

    Modelled probability that a player-season leads to being drafted.

    :param name: Player name, matched case-insensitively.
    :param season: One season. Defaults to their most recent.
    :return: Probability in [0, 1], or None if not in the eligible population.

.. py:function:: predict_draft_order(name: str, season: int | None = None) -> float | None

    Modelled position within the college portion of a draft class. Lower is
    better; floored at 1, since the regressor is unbounded and a standout
    otherwise extrapolates past the top of the board.

    :param name: Player name, matched case-insensitively.
    :param season: One season. Defaults to their most recent.
    :return: Predicted order, or None.

.. py:function:: is_draft_eligible(name: str, season: int | None = None) -> tuple[bool, str] | None

    Whether a player was draft eligible, and on what basis.

    Eligibility is **inferred**, not looked up — from seasons completed and from
    age, which is itself estimated for most players. The basis says which
    evidence was used: ``"drafted"``, ``"class"``, ``"age"``, ``"unknown"``, or
    ``"ineligible"``.

    :param name: Player name, matched case-insensitively.
    :param season: One season. Defaults to their most recent.
    :return: ``(eligible, basis)``, or None.

.. py:function:: scouting_report(name: str, season: int | None = None, *, top_n: int = 5) -> str | None

    A readable scouting report: grade, projected draft position, eligibility,
    actual outcome if known, and the inputs pushing the prediction each way.

    :param name: Player name, matched case-insensitively.
    :param season: One season. Defaults to their most recent.
    :param top_n: How many strengths and concerns to list.
    :return: The formatted report, or None.

.. py:function:: explain_prediction(name: str, season: int | None = None, *, top_n: int = 5, method: ["auto", "shap", "gain"] = "auto") -> dict | None

    Which inputs pushed a player's draft probability up or down, in percentage
    points of probability.

    :param name: Player name, matched case-insensitively.
    :param season: One season. Defaults to their most recent.
    :param top_n: How many strengths and concerns to return.
    :param method: "shap" for exact attributions, "gain" for the fallback,
                   "auto" to prefer SHAP when installed.
    :return: ``method``, ``draft_probability``, ``strengths``, ``concerns``.

.. py:function:: predict_from_stats(role: ["batter", "pitcher", "two_way"], age: float, stats: dict, *, team: str | None = None, season: int | None = None, name: str = "Custom player") -> dict

    Score a stat line that is not in the data.

    Supply as much or as little as you have — unspecified player statistics stay
    missing, which the models handle natively. Team context comes from the named
    program, or the season median. The result reports how much was imputed and a
    ``confidence`` band, because a four-statistic line is not the same evidence
    as a full season.

    :param role: "batter", "pitcher", or "two_way".
    :param age: Player age during the season.
    :param stats: Any subset of feature names, e.g. ``{"era_pitch": 2.4, "so_pitch": 130}``.
    :param team: Any spelling of a team name, for context.
    :param season: Season for team context and league constants. Defaults to
                   the most recent in the data.
    :param name: Label used in the report.
    :return: ``draft_probability``, ``draft_grade``, ``predicted_order``,
             ``imputed_features``, ``confidence``, ``report``.

.. py:function:: draft_board(season: int, *, n: int = 100, min_probability: float = 0.0) -> list[dict]

    Rank a season's eligible players by modelled draft probability.

    :param season: Season year.
    :param n: How many players to return.
    :param min_probability: Drop players below this probability.
    :return: ``rank``, ``name``, ``team``, ``draft_probability``,
             ``draft_grade``, ``predicted_order``, ``actual_pick``.

.. py:function:: model_card(stage: int | None = None) -> dict

    Provenance, held-out performance, and limitations of the shipped models.
    Published as a function, not a docs footnote, so the numbers travel with the
    predictions.

    :param stage: Restrict to one stage.
    :return: The manifest plus ``limitations`` and reference-implementation
             numbers for comparison.

Performance
-----------

Trained on 2021-2025, tested on the held-out 2026 season. 25,324 draft-eligible
player-seasons; 7.8% of the held-out season was drafted.

============  ==========  =========================================
Stage         Metric      Value
============  ==========  =========================================
1 (drafted)   PR-AUC      0.703   (random baseline 0.078)
1 (drafted)   ROC-AUC     0.957
2 (order)     Spearman    0.647
2 (order)     MAE         78 places
============  ==========  =========================================

.. note::

   The held-out season is the most recent one with complete draft labels, so it
   moves forward with each release. Version 1.2.0 tested on 2025 and scored
   marginally higher (PR-AUC 0.708, ROC-AUC 0.962, Spearman 0.644). That is a
   property of the sample rather than a regression: 2026 is a harder season for
   the model, and the two numbers are not comparable to each other.

For orientation, the research model this one derives from — V7, Biggs & Gerber
(2026) — reported PR-AUC 0.725, ROC-AUC 0.949, and Spearman 0.653 on the same
2026 test year. Those are **not this package's numbers**. V7 used proprietary
third-party metrics as features, along with a different label set, population,
and hyperparameters, so the gap between the two cannot be attributed to any one
of those. :func:`model_card` carries the full comparison and the lineage.

Limitations
-----------

- **Stage 1 precision depends on the base rate** of the population you apply it
  to. About 7.8% of eligible players were drafted in the held-out season.
  Applied to a pre-screened shortlist precision is higher; applied to every
  player in the country, lower.
- **Eligibility is inferred**, from seasons completed and from age — and age is
  estimated for most players. :func:`is_draft_eligible` returns the basis so the
  inference is visible.
- **The order model is trained only on drafted players.** Below a 25% draft
  probability it is extrapolating, and the output is suppressed rather than
  printed.
- **One held-out season** (2026), not a cross-validated estimate.
- **Order predictions are noisy.** A mean absolute error of 78 places means this
  separates tiers, not picks.

Usage
-----

.. code-block:: python

    from ncaa_bbStats import (
        scouting_report, predict_from_stats, draft_board, model_card,
    )

    print(scouting_report("Kade Anderson", 2025))

    # Score a line that is not in the data
    result = predict_from_stats(
        "pitcher", age=21,
        stats={"era_pitch": 2.40, "so_pitch": 130, "bb_pitch": 25,
               "ip_pitch": 95.0, "h_pitch": 68, "hr_pitch": 5},
        team="LSU", season=2025, name="Prospect A",
    )
    print(result["report"])
    result["confidence"]        # 'low' -- only 9 of 72 inputs supplied

    # A whole season, ranked
    for row in draft_board(2025, n=10):
        print(row["rank"], row["name"], row["draft_probability"],
              "actual", row["actual_pick"])

    model_card()["limitations"]

Data Source
-----------

``src/data/models/`` — two XGBoost boosters in native UBJSON, a manifest
recording the exact feature order, and the training matrix, so the models can be
refitted from the wheel alone::

    python -m ncaa_bbStats.model_store

See Also
--------

- :doc:`draft_detail`
- :doc:`prospects`
- :doc:`advanced_stats`
- :doc:`data_provenance`

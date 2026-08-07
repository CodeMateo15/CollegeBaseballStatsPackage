Advanced Stats
==============

Run-value metrics derived by this package from NCAA counting statistics, using
linear weights regressed from the packaged team-stats cache.

Overview
--------

The player cache stores counting statistics only. Everything on this page is
computed when you read it, which is why the numbers can never fall out of step
with the data they come from.

Metrics are prefixed ``c`` for *college-calibrated*. They are constructed the
same way as the familiar sabermetric statistics, but their league constants come
from NCAA play rather than from Major League Baseball or a vendor's proprietary
values. They correlate very closely with their namesakes (0.95-1.00; see
:doc:`data_provenance`) but are not interchangeable with them.

You will usually reach these through :doc:`player_stats`::

    batting_stat("Jack Goodman", "cwrc+", year=2025)
    pitching_stat("Aiven Cabral", "cfip", year=2025)

The functions below take a dict of counting stats and are useful when you have a
stat line that is not in the cache -- a prospective player, or a partial season.

How the weights are derived
---------------------------

For each season and division, a weighted least-squares regression of team runs
scored on team event rates::

    PA = AB + BB + HBP + SF
    y  = R / PA
    X  = [1B, 2B, 3B, HR, BB, HBP, SB, CS] / PA        weight = PA

Outs are the omitted category, so each coefficient is the marginal runs from
turning one out into that event. Fit quality is R² 0.96-0.98 on runs scored,
RMSE about 16 runs against seasons averaging 300.

Season estimates are then shrunk toward the division's pooled value, because the
season-to-season spread of the raw coefficients is about the size of their
standard errors -- most of the movement is sampling noise. Finally the hit-type
weights are projected onto the ordering physics requires (1B ≤ 2B ≤ 3B ≤ HR); an
unconstrained fit puts the triple above the home run in 34 of 55
division-seasons, because triples are too rare to estimate cleanly.

.. note::

   Weights exist from 2008 for Divisions I and II, and from 2009 for Division
   III (excluding 2011). Seasons 2002-2007 record only at-bats, hits and runs,
   which is not enough to fit. Metrics return ``None`` for those seasons rather
   than a fabricated value.

Batting Functions
-----------------

.. py:function:: cwoba(stats: dict, year: int, division: int = 1) -> float | None

    College wOBA: one number for a hitter's total offensive value per plate
    appearance, weighting each way of reaching base by its run value. Scaled so
    the league average equals league OBP.

    :param stats: Counting stats with ``ab``, ``h``, ``2b``, ``3b``, ``hr``, ``bb``, ``hbp``, ``sf``.
    :param year: Season year.
    :param division: NCAA division (1, 2, or 3).
    :return: cwOBA, or None if the season has no constants or an input is missing.

.. py:function:: cwraa(stats: dict, year: int, division: int = 1) -> float | None

    Runs contributed above a league-average hitter. Zero is exactly average.

    :param stats: Counting stats, as for ``cwoba``, plus ``pa``.
    :param year: Season year.
    :param division: NCAA division (1, 2, or 3).
    :return: Runs above average, or None.

.. py:function:: cwrc(stats: dict, year: int, division: int = 1) -> float | None

    Total runs the hitter is responsible for producing.

    :param stats: Counting stats, as for ``cwraa``.
    :param year: Season year.
    :param division: NCAA division (1, 2, or 3).
    :return: Runs created, or None.

.. py:function:: cwrc_plus(stats: dict, year: int, division: int = 1) -> float | None

    Weighted Runs Created indexed so 100 is league average. 130 means 30% better
    than an average hitter that season. Indexed to its own season, so it compares
    hitters across different run environments.

    No park adjustment is applied; park factors are fixed at 1.0 because NCAA
    park data is not publicly available. Hitters at extreme-altitude programs are
    flattered as a result.

    :param stats: Counting stats, as for ``cwraa``.
    :param year: Season year.
    :param division: NCAA division (1, 2, or 3).
    :return: Index where 100 is league average, or None.

.. py:function:: cwsb(stats: dict, year: int, division: int = 1) -> float | None

    Stolen-base runs above average. Credits steals and debits times caught at
    their measured NCAA run values, then subtracts what a league-average runner
    would produce from the same number of times on base -- so a runner who steals
    often but is caught often can still land below zero.

    :param stats: Counting stats with ``sb``, ``cs``, and the on-base components.
    :param year: Season year.
    :param division: NCAA division (1, 2, or 3).
    :return: Baserunning runs above average, or None.

.. py:function:: cspd(stats: dict) -> float | None

    Bill James Speed Score, a 0-10 estimate of baserunning speed from the box
    score. Needs no league constant.

    Its constants were fitted to Major League play, so NCAA hitters average about
    3.9 rather than the conventional 5.0. Compare players to each other, not to
    the usual scale. Informational only.

    :param stats: Counting stats with ``sb``, ``cs``, ``3b``, ``ab``, ``hr``, ``so``, ``r``, ``h``, ``bb``.
    :return: Speed score in [0, 10], or None.

Pitching Functions
------------------

.. py:function:: cfip(stats: dict, year: int, division: int = 1) -> float | None

    Fielding independent pitching, on the ERA scale. Judges a pitcher only on
    strikeouts, walks, hit batters and home runs -- the outcomes independent of
    the defence behind them.

    :param stats: Counting stats with ``ip``, ``hr``, ``bb``, ``so``, optionally ``hbp``.
    :param year: Season year.
    :param division: NCAA division (1, 2, or 3).
    :return: cFIP on the ERA scale, or None.

.. py:function:: clob_pct(stats: dict) -> float | None

    Share of baserunners stranded. Needs no league constant.

    :param stats: Counting stats with ``h``, ``bb``, ``r``, ``hr``, optionally ``hbp``.
    :return: Strand rate as a proportion, or None if the denominator is non-positive.

Constants
---------

.. py:function:: league_constants(year: int, division: int = 1, kind: ["batting", "pitching"] = "batting") -> dict | None

    Return the league constants for one season and division -- the run values,
    scaling terms, and fit diagnostics behind every metric above.

    :param year: Season year.
    :param division: NCAA division (1, 2, or 3).
    :param kind: "batting" for run values and scaling, "pitching" for the FIP constant.
    :return: The constants row as a dict, or None if that season has none.

.. py:function:: seasons_with_constants(division: int = 1, kind: ["batting", "pitching"] = "batting") -> list[int]

    List the seasons that have league constants for a division.

    :param division: NCAA division (1, 2, or 3).
    :param kind: "batting" or "pitching".
    :return: Sorted season years.

.. py:function:: ip_to_float(value) -> float | None

    Convert NCAA innings notation to true innings. NCAA writes thirds as tenths,
    so ``97.2`` means 97 and two-thirds, not 97.2. Reading it as a decimal
    inflates every innings-denominated rate.

    :param value: Innings pitched as reported.
    :return: Innings as a real number, or None.

Usage
-----

.. code-block:: python

    from ncaa_bbStats import cwrc_plus, cfip, league_constants, batting_stat

    # Through the player cache
    batting_stat("Jack Goodman", "cwrc+", year=2025)   # 119.5

    # From a stat line that is not in the cache
    line = {"ab": 203, "h": 68, "2b": 17, "3b": 1, "hr": 10,
            "bb": 26, "hbp": 5, "sf": 0, "pa": 234}
    cwrc_plus(line, 2025, division=1)

    # Inspect the run values behind it
    c = league_constants(2025, 1)
    print(c["w_1b"], c["w_hr"], c["lg_obp"])

Download
--------

:download:`batting_weights.csv <_static/data/league_constants/batting_weights.csv>`

:download:`pitching_constants.csv <_static/data/league_constants/pitching_constants.csv>`

See Also
--------

- :doc:`player_stats`
- :doc:`player_reference`
- :doc:`data_provenance`

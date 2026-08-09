Leaderboards
============

Top-N lists over player seasons and careers, sorted the right way round.

Overview
--------

:func:`leaderboard` replaces :func:`top_players`, which sorts descending
unconditionally -- so asking it for the top ERA returns the *worst* pitchers in
the country::

    >>> top_players("pitching", "era", 3, 2025)          # the old behaviour
    [{'name': 'Jermel Ford', 'value': 13.99}, ...]

    >>> leaderboard("era", stat_type="pitching", year=2025, n=3, min_ip=50)
    [{'name': 'Jack Ohman', 'value': 1.344}, ...]

Direction is taken from the statistic, and the table is inspectable via
:func:`stat_direction`. It knows that strikeouts are good for a pitcher and bad
for a hitter. Pass ``ascending=`` to override.

Any statistic works -- counting, rate, or advanced -- because rates are computed
on read. Team names resolve through :doc:`team_registry`, so ``"Auburn"``,
``"AUB"`` and ``"Auburn University"`` are interchangeable.

Functions
---------

.. py:function:: leaderboard(stat: str, *, stat_type: ["batting", "pitching"] = "batting", year: int | None = None, years: Sequence[int] | None = None, team: str | None = None, conference: str | None = None, n: int = 10, ascending: bool | None = None, qualifier: ["qualified", "noMin"] = "qualified", min_pa: int | None = None, min_ip: float | None = None, per: ["season", "career"] = "season", include: Sequence[str] | None = None) -> list[dict]

    Top N players by any statistic.

    :param stat: Column name, matched case-insensitively.
    :param stat_type: "batting" or "pitching".
    :param year: A single season.
    :param years: Several seasons. Ignored if ``year`` is given.
    :param team: Any spelling of a team name.
    :param conference: Conference code, e.g. "SEC".
    :param n: How many rows. Pass None for all.
    :param ascending: Force a sort direction. Defaults to :func:`stat_direction`.
    :param qualifier: "qualified" or "noMin".
    :param min_pa: Additional plate-appearance floor.
    :param min_ip: Additional innings floor, in true innings.
    :param per: "season" for one row per player-season, "career" to aggregate first.
    :param include: Extra columns to carry into each row.
    :return: Dicts with ``name``, ``team``, ``year``, ``value``, plus extras.

.. py:function:: stat_direction(stat: str, stat_type: ["batting", "pitching"] = "batting") -> str

    Whether a higher or lower value is the better performance.

    :param stat: Column name, matched case-insensitively.
    :param stat_type: "batting" or "pitching". Some stats point opposite ways.
    :return: ``"higher"`` or ``"lower"``.

.. py:function:: qualification_rules(stat_type: ["batting", "pitching"], year: int | None = None) -> dict

    The playing-time minimums behind ``qualifier="qualified"`` -- 2 plate
    appearances or 0.7 innings per team game. Applied per team game, so the
    absolute bar moves with the schedule.

    ``observed_minimum`` is measured from the shipped data rather than assumed,
    so the documented rule and the actual population cannot drift apart.

    :param stat_type: "batting" or "pitching".
    :param year: Restrict the observed minimum to one season.
    :return: ``per_game``, ``basis``, ``observed_minimum``,
             ``typical_season_games``, ``typical_threshold``.

Career leaderboards
-------------------

``per="career"`` aggregates a player's seasons before ranking. Counting stats
are summed; rates are rebuilt from the summed components, so a career ERA is
total earned runs over total innings rather than an average of season ERAs.
Innings are summed in thirds, not as decimals.

.. code-block:: python

    >>> leaderboard("hr", per="career", n=3, qualifier="noMin")
    [{'name': 'Jac Caglianone', 'value': 75.0, 'seasons': 3}, ...]

    >>> leaderboard("era", stat_type="pitching", per="career",
    ...             n=3, min_ip=150, qualifier="noMin")
    [{'name': 'Paul Skenes', 'value': 2.183, 'seasons': 3}, ...]

Usage
-----

.. code-block:: python

    from ncaa_bbStats import leaderboard

    # Best ERA in the SEC, with a real innings floor
    leaderboard("era", stat_type="pitching", year=2025,
                conference="SEC", min_ip=60, n=10)

    # Most productive hitters by the package's own run-value metric
    leaderboard("cwrc+", year=2025, n=10, include=["hr", "ops"])

    # One program's leaders
    leaderboard("hr", year=2025, team="Auburn", n=5)

See Also
--------

- :doc:`player_stats`
- :doc:`advanced_stats`
- :doc:`team_registry`

RPI and Schedule Strength
=========================

Ratings Percentage Index, strength of schedule, and quadrant records.

Overview
--------

.. note::

   RPI is **Warren Nolan's computation** from public game results, not an
   official NCAA statistic. Do not cite it as one.

Coverage is Division I from 2021. Warren Nolan does not publish earlier years,
so functions return ``None`` outside that range rather than raising -- the gap
is permanent, not a backlog.

RPI and SOS are stored as **ranks**, where 1 is best.

Quadrants group opponents by strength, Q1 being the toughest. A team's Q1 record
is the usual shorthand for how it fared against good competition.

Functions
---------

.. py:function:: rpi_rank(team: str, season: int) -> int | None

    A team's RPI rank, where 1 is the best in Division I.

    :param team: Any spelling of a team name.
    :param season: Season year (2021-2026).
    :return: The rank, or None.

.. py:function:: rpi(team: str, season: int) -> int | None

    Alias for :func:`rpi_rank`.

    :param team: Any spelling of a team name.
    :param season: Season year (2021-2026).
    :return: The rank, or None.

.. py:function:: strength_of_schedule(team: str, season: int) -> int | None

    Strength-of-schedule rank, where 1 is the toughest schedule played.

    :param team: Any spelling of a team name.
    :param season: Season year (2021-2026).
    :return: The rank, or None.

.. py:function:: rpi_record(team: str, season: int) -> dict | None

    A team's full RPI profile: ranks, splits, and every quadrant record.

    :param team: Any spelling of a team name.
    :param season: Season year (2021-2026).
    :return: All stored fields, or None.

.. py:function:: rpi_table(season: int, *, conference: str | None = None, n: int | None = None) -> list[dict]

    The RPI standings for a season.

    :param season: Season year (2021-2026).
    :param conference: Restrict to one conference.
    :param n: Return only the top N.
    :return: Rows ordered by RPI rank, best first.

.. py:function:: quadrant_record(team: str, season: int, quadrant: int) -> dict | None

    A team's record against one quadrant of opponents.

    :param team: Any spelling of a team name.
    :param season: Season year (2021-2026).
    :param quadrant: 1, 2, 3, or 4.
    :return: ``wins``, ``losses``, ``win_pct``, or None.

.. py:function:: home_road_neutral(team: str, season: int) -> dict | None

    Home, road, and neutral-site records.

    :param team: Any spelling of a team name.
    :param season: Season year (2021-2026).
    :return: One entry per venue type, each with ``wins``, ``losses``, ``win_pct``.

.. py:function:: nonconference_profile(team: str, season: int) -> dict | None

    Non-conference record, and how hard that schedule was.

    :param team: Any spelling of a team name.
    :param season: Season year (2021-2026).
    :return: ``wins``, ``losses``, ``win_pct``, ``rpi_rank``, ``sos_rank``.

.. py:function:: rpi_over_years(team: str, start: int = 2021, end: int = 2026) -> list[dict]

    A team's RPI and schedule strength season by season.

    :param team: Any spelling of a team name.
    :param start: First season.
    :param end: Last season.
    :return: One dict per season with data.

.. py:function:: best_wins(season: int, *, n: int = 25) -> list[dict]

    Teams with the most Quadrant 1 wins -- the best wins against good teams.

    :param season: Season year (2021-2026).
    :param n: How many teams to return.
    :return: ``team_name``, ``conference``, ``q1_wins``, ``q1_losses``, ``rpi_rank``.

Usage
-----

.. code-block:: python

    from ncaa_bbStats import rpi_rank, quadrant_record, rpi_table, best_wins

    rpi_rank("Tennessee", 2024)              # 1
    strength_of_schedule("Tennessee", 2024)  # 12
    quadrant_record("Tennessee", 2024, 1)    # {'wins': 26, 'losses': 10, ...}

    # Who beat the most good teams?
    [(r["team_name"], r["q1_wins"]) for r in best_wins(2025, n=5)]

    # Conference standings by RPI
    rpi_table(2025, conference="SEC")

Data Source
-----------

``src/data/rpi/{season}.csv``. Read by ``ncaa_bbStats.rpi_utils``,
written by ``ncaa_bbStats.rpi_store`` -- see :doc:`regenerating`.

See Also
--------

- :doc:`team_registry`
- :doc:`crossref`
- :doc:`data_provenance`

Program Finances
================

Baseball program budgets, revenue, and staffing, from the federal EADA survey.

Overview
--------

Source: the Equity in Athletics Disclosure Act survey, U.S. Department of
Education. Every co-educational institution receiving Title IV funding must file
annually, so coverage is close to complete: about 99% of Division I and 69% of
Divisions II and III.

.. note::

   Budget figures are **percentiles within a reporting year**, not dollars.
   Baseball budgets inflate a few percent annually, so raw figures are not
   comparable across seasons; a percentile is. 0.95 means the program outspends
   95% of filers.

.. note::

   Institutions file the 2025-26 survey in October 2026, so the **2026 season
   carries 2025 forward**. Every such row reports ``carried_forward=True`` and
   an ``eada_year`` of 2025 — a carried-forward figure quietly treated as
   current is how wrong conclusions get published.

Reported rosters outside 15-75 players are treated as unreported: a few
institutions file a system-wide row summing every branch campus, which shows up
as one program carrying 453 baseball players.

Functions
---------

.. py:function:: program_finance(team: str, season: int) -> dict | None

    A program's baseball finances for one season: twelve derived features plus
    ``eada_year`` and ``carried_forward``.

    :param team: Any spelling of a team name.
    :param season: Season year (2021-2026).
    :return: The record, or None if the program has no filing that season.

.. py:function:: budget_percentile(team: str, season: int) -> float | None

    Where a program's baseball budget ranks among all filers that year, in [0, 1].

    :param team: Any spelling of a team name.
    :param season: Season year (2021-2026).
    :return: The percentile, or None.

.. py:function:: roster_size(team: str, season: int) -> float | None

    Number of baseball participants reported.

    :param team: Any spelling of a team name.
    :param season: Season year (2021-2026).
    :return: Participants, or None if unreported or implausible.

.. py:function:: coaching_staff_size(team: str, season: int) -> float | None

    Head plus assistant baseball coaches reported.

    :param team: Any spelling of a team name.
    :param season: Season year (2021-2026).
    :return: Coach count, or None.

.. py:function:: richest_programs(season: int, *, n: int = 25, division: int | None = None) -> list[dict]

    The highest-spending baseball programs in a season.

    :param season: Season year (2021-2026).
    :param n: How many to return.
    :param division: Restrict to one NCAA division.
    :return: Programs sorted by budget percentile.

.. py:function:: conference_spending(season: int, *, division: int = 1) -> list[dict]

    Median baseball budget percentile by conference.

    :param season: Season year (2021-2026).
    :param division: NCAA division.
    :return: ``conference``, ``programs``, ``median_budget_pct``, richest first.

.. py:function:: finance_vs_rpi(season: int, *, division: int = 1) -> list[dict]

    Program spending beside on-field results, ready for correlation work.

    :param season: Season year (2021-2026).
    :param division: NCAA division.
    :return: One row per program with both a budget percentile and an RPI rank.

Derived features
----------------

- ``budget_pct`` -- baseball operating-expense percentile
- ``log_budget`` -- log of baseball operating expenses
- ``opex_per_player_pct``, ``log_opex_per_player`` -- operating expense per participant
- ``log_budget_per_player`` -- expenses divided by roster size
- ``roster_size`` -- reported participants
- ``log_revenue``, ``net_revenue`` -- baseball revenue, and revenue minus expenses
- ``coaching_staff_size`` -- head plus assistant coaches
- ``dept_recruiting_pct``, ``log_dept_recruiting`` -- men's recruiting spend (department-wide)
- ``log_dept_coach_salary`` -- average head-coach salary (department-wide, men's)

Usage
-----

.. code-block:: python

    from ncaa_bbStats import program_finance, richest_programs, finance_vs_rpi

    program_finance("Tennessee", 2025)
    # budget_pct 1.000, roster_size 55, coaching_staff_size 4

    program_finance("Tennessee", 2026)["carried_forward"]   # True

    [r["institution_name"] for r in richest_programs(2025, n=3, division=1)]
    # Tennessee, LSU, Vanderbilt

    # Does spending buy wins?
    rows = finance_vs_rpi(2025)

Data Source
-----------

``src/data/program_finance/eada_features.csv``, derived by
``ncaa_bbStats.program_store`` from https://ope.ed.gov/athletics/. The source
workbooks are roughly 100 MB each and are not shipped.

See Also
--------

- :doc:`crossref`
- :doc:`data_provenance`

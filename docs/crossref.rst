Cross-Dataset Queries
=====================

Questions that need several datasets at once.

Overview
--------

Every function here is a hand-written join, not a generic query engine. Each
answers one question well and reports which datasets it could reach, so a
missing section reads as missing rather than as zero.

All of it depends on :doc:`team_registry` to reconcile the different ways these
sources spell school names.

Functions
---------

.. py:function:: team_profile(team: str, season: int) -> dict | None

    Everything the package knows about one program in one season: identity, NCAA
    team statistics, RPI and schedule strength, conference, program finances,
    that year's draft class, and Pythagorean expectation.

    Sections the package cannot reach are ``None`` rather than absent, and a
    ``coverage`` key reports which are populated.

    :param team: Any spelling of a team name.
    :param season: Season year.
    :return: Keys ``identity``, ``record``, ``stats``, ``rpi``, ``finance``,
             ``draft``, ``pythagorean``, ``coverage``. None if unresolvable.

.. py:function:: player_profile(name: str, season: int | None = None) -> dict | None

    Everything the package knows about one player: batting and pitching lines,
    their program's context, the draft record if they were selected, and their
    pre-draft ranking.

    :param name: Player name, matched case-insensitively.
    :param season: One season. Defaults to their most recent.
    :return: Keys ``name``, ``season``, ``role``, ``batting``, ``pitching``,
             ``team``, ``draft``, ``prospect_rank``, ``coverage``. None if the
             player is not in the cache.

.. py:function:: draft_yield(team: str, start: int = 2021, end: int = 2026) -> dict | None

    How many players a program put into the draft, and for how much.

    :param team: Any spelling of a team name.
    :param start: First draft year.
    :param end: Last draft year.
    :return: ``picks``, ``picks_per_year``, ``first_round_picks``,
             ``top_ten_round_picks``, ``total_bonus_dollars``, ``best_pick``,
             ``by_year``.

.. py:function:: dollars_per_draft_pick(team: str, start: int = 2021, end: int = 2025) -> dict | None

    Program spending set against the players it produced.

    Budget is a percentile, not dollars, so this is not a literal cost per pick —
    it pairs spending rank with draft output, which is the comparison that
    travels across seasons.

    :param team: Any spelling of a team name.
    :param start: First season.
    :param end: Last season. Defaults to 2025, the last surveyed year.
    :return: ``mean_budget_pct``, ``picks``, ``picks_per_year``,
             ``bonus_dollars_per_year``, ``seasons_with_finance``.

.. py:function:: conference_report(conference: str, season: int) -> dict

    A conference's members, standings, spending, and draft output.

    :param conference: Conference code, e.g. "SEC".
    :param season: Season year.
    :return: ``programs``, ``members``, ``standings``, ``draft_picks``,
             ``bonus_dollars``, ``median_budget_pct``, ``best_rpi_rank``.

.. py:function:: pipeline(team: str, start: int = 2021, end: int = 2026) -> list[dict]

    A program's season-by-season timeline across every dataset — conference,
    record, RPI, budget percentile, draft picks. Built for plotting a
    trajectory.

    :param team: Any spelling of a team name.
    :param start: First season.
    :param end: Last season.
    :return: One dict per season with any data.

.. py:function:: compare_teams(teams: Sequence[str], season: int) -> list[dict]

    Several programs side by side for one season, as flat rows.

    :param teams: Team names in any spelling.
    :param season: Season year.
    :return: One row per resolvable team, in the order given.

Usage
-----

.. code-block:: python

    from ncaa_bbStats import team_profile, player_profile, pipeline

    p = team_profile("Tennessee", 2024)
    p["record"]              # 60-13, .822
    p["rpi"]["rpi_rank"]     # 1
    p["draft"]["picks"]      # 8
    p["pythagorean"]         # expected .807 vs actual .822

    player_profile("Kade Anderson")
    # pitcher, LSU (SEC), 2025: 3.18 ERA, 180 K in 119 IP
    # drafted 3rd overall, $8,800,000; ranked 2nd pre-draft

    # A program's trajectory
    for row in pipeline("Coastal Carolina"):
        print(row["season"], row["wins"], row["rpi_rank"], row["draft_picks"])

Recipes
-------

**Which conference produces the most draft picks per dollar spent?**

.. code-block:: python

    from ncaa_bbStats import conference_draft_counts, conference_spending

    picks = {c["conference"]: c["picks"] for c in conference_draft_counts(2025)}
    for row in conference_spending(2025)[:10]:
        n = picks.get(row["conference"], 0)
        print(f"{row['conference']:12s} budget {row['median_budget_pct']:.3f} "
              f"-> {n:3d} picks")

**Do high-RPI programs draft better than their record suggests?**

.. code-block:: python

    from ncaa_bbStats import finance_vs_rpi, draft_yield

    for row in finance_vs_rpi(2025)[:25]:
        y = draft_yield(row["team_id"], 2025, 2025)
        print(f"{row['institution_name'][:28]:28s} RPI {row['rpi_rank']:3d} "
              f"budget {row['budget_pct']:.3f}  {y['picks']} picks")

**Which teams won more than their run differential deserved?**

.. code-block:: python

    from ncaa_bbStats import luckiest_teams, rpi_rank

    for row in luckiest_teams(2025, n=10):
        print(f"{row['team']:20s} +{row['luck_wins']:.1f} wins  "
              f"RPI {rpi_rank(row['team'], 2025)}")

See Also
--------

- :doc:`team_registry`
- :doc:`rpi`
- :doc:`program_finance`
- :doc:`draft_detail`

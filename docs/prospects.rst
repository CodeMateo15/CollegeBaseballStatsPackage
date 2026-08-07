Draft Prospects
===============

MLB Pipeline top-250 pre-draft rankings, 2021-2026.

Overview
--------

Third-party scouting rankings published before each draft. Their value here is
as a benchmark: how a consensus board compares against where players actually
went, and against any model's ordering.

College prospects resolve to a canonical ``team_id``. High schoolers have no
college program and are flagged ``is_college=False`` rather than forced onto one.

Functions
---------

.. py:function:: prospect_rank(name: str, season: int) -> int | None

    A player's pre-draft ranking on the top-250 board.

    :param name: Player name, matched case-insensitively.
    :param season: Draft year (2021-2026).
    :return: The rank, or None if unranked.

.. py:function:: prospect_board(season: int, *, n: int | None = None, position: str | None = None, team: str | None = None, college_only: bool = False) -> list[dict]

    The prospect board for a draft year.

    :param season: Draft year (2021-2026).
    :param n: Return only the top N.
    :param position: Filter by position, e.g. "RHP".
    :param team: Any spelling of a college team name.
    :param college_only: Exclude high-school prospects.
    :return: Prospects in ranking order.

.. py:function:: prospect_vs_actual(season: int) -> list[dict]

    Pre-draft ranking against actual selection. A positive ``surprise`` means the
    player went earlier than the board had them.

    :param season: Draft year (2021-2026).
    :return: Players on both the board and the draft record, by actual pick.

.. py:function:: biggest_draft_risers(season: int, *, n: int = 15) -> list[dict]

    Players selected much earlier than their pre-draft ranking.

    :param season: Draft year (2021-2026).
    :param n: How many to return.
    :return: Rows from :func:`prospect_vs_actual`, biggest rise first.

.. py:function:: biggest_draft_fallers(season: int, *, n: int = 15) -> list[dict]

    Players who slid well past their pre-draft ranking.

    :param season: Draft year (2021-2026).
    :param n: How many to return.
    :return: Rows from :func:`prospect_vs_actual`, biggest slide first.

Usage
-----

.. code-block:: python

    from ncaa_bbStats import prospect_rank, prospect_vs_actual, biggest_draft_fallers

    prospect_rank("Kade Anderson", 2025)     # 2, and he went 3rd

    # How well did the consensus board predict the draft?
    rows = prospect_vs_actual(2025)
    import statistics
    statistics.correlation(
        [r["prospect_rank"] for r in rows],
        [r["actual_pick"] for r in rows],
    )

    # Who slid?
    [(r["name"], r["prospect_rank"], r["actual_pick"])
     for r in biggest_draft_fallers(2025, n=3)]

Data Source
-----------

``src/data/prospects/{season}.csv``. Read by
``ncaa_bbStats.prospect_utils``, written by ``ncaa_bbStats.prospect_store`` --
see :doc:`regenerating`.

See Also
--------

- :doc:`draft_detail`
- :doc:`data_provenance`

Draft Detail
============

Signing bonuses, slot values, and player biography from the MLB Stats API.

Overview
--------

Adds the detail the Baseball Almanac cache does not carry. Covers 2021-2026;
:doc:`mlb_draft` remains the way to reach 1965-2025 draft history.

Each pick records the signing bonus, the published slot value, school and class
(``"4YR JR"``, ``"JC J2"``), birth date, height, weight, position, handedness,
and the drafting club.

.. note::

   MLB assigns slot values for the first ten rounds only. Picks after round ten
   have no published slot and return ``None`` -- the API reports the string
   ``"0"`` there, which would otherwise read as a slot value of nothing rather
   than no slot at all.

Functions
---------

.. py:function:: draft_pick(season: int, pick: int) -> dict | None

    Look up one pick by overall selection number.

    :param season: Draft year (2021-2026).
    :param pick: Overall pick number, 1 being first.
    :return: The pick record, or None.

.. py:function:: slot_value(season: int, pick: int) -> int | None

    The published bonus slot value for a pick, in dollars.

    :param season: Draft year (2021-2026).
    :param pick: Overall pick number.
    :return: Dollars, or None if the pick has no published slot.

.. py:function:: signing_bonus(name: str, season: int) -> int | None

    A drafted player's signing bonus, in dollars.

    :param name: Player name, matched case-insensitively.
    :param season: Draft year (2021-2026).
    :return: Dollars, or None if not found or unsigned.

.. py:function:: bonus_vs_slot(name: str, season: int) -> float | None

    Ratio of signing bonus to slot value. Above 1.0 means the player signed over
    slot, usually because they had leverage such as remaining college
    eligibility.

    :param name: Player name, matched case-insensitively.
    :param season: Draft year (2021-2026).
    :return: The ratio, or None.

.. py:function:: draft_class(team: str, season: int) -> list[dict]

    Every player drafted out of a program in one year.

    :param team: Any spelling of a college team name.
    :param season: Draft year (2021-2026).
    :return: Picks in selection order.

.. py:function:: draft_history(team: str, start: int = 2021, end: int = 2026) -> list[dict]

    Every player drafted out of a program across several years.

    :param team: Any spelling of a college team name.
    :param start: First draft year.
    :param end: Last draft year.
    :return: Picks ordered by year then selection.

.. py:function:: draft_board(season: int, *, n: int | None = None, college_only: bool = False) -> list[dict]

    The draft in selection order.

    :param season: Draft year (2021-2026).
    :param n: Return only the first N picks.
    :param college_only: Exclude high-school selections.
    :return: Picks in order.

.. py:function:: biggest_bonuses(season: int, *, n: int = 25) -> list[dict]

    The largest signing bonuses in a draft class.

    :param season: Draft year (2021-2026).
    :param n: How many to return.
    :return: Picks sorted by bonus, largest first.

.. py:function:: overslot_picks(season: int, *, min_ratio: float = 1.05, n: int | None = None) -> list[dict]

    Players who signed for meaningfully more than their pick's slot value.

    :param season: Draft year (2021-2026).
    :param min_ratio: Minimum bonus-to-slot ratio to include.
    :param n: Return only the top N.
    :return: Picks with a ``bonus_slot_ratio`` field.

.. py:function:: draft_demographics(season: int) -> dict

    Summary of a draft class: counts by origin (four-year, junior college, high
    school), by class, by position, plus mean age and total bonus dollars.

    :param season: Draft year (2021-2026).
    :return: The summary.

.. py:function:: conference_draft_counts(season: int, *, division: int = 1) -> list[dict]

    How many players each conference produced.

    :param season: Draft year (2021-2026).
    :param division: NCAA division to attribute programs by.
    :return: ``conference``, ``picks``, ``bonus_dollars``, sorted by picks.

.. py:function:: state_pipeline(state: str, *, start: int = 2021, end: int = 2026) -> list[dict]

    Players drafted out of schools in one state, by year.

    :param state: Two-letter state code, e.g. "TX".
    :param start: First draft year.
    :param end: Last draft year.
    :return: One dict per year with ``picks``, ``bonus_dollars``, ``top_pick``.

Usage
-----

.. code-block:: python

    from ncaa_bbStats import draft_pick, draft_class, conference_draft_counts

    p = draft_pick(2024, 1)
    # Travis Bazzana, Oregon State, 4YR JR
    # $8,950,000 bonus against a $10,570,600 slot

    draft_class("LSU", 2025)
    # Kade Anderson (#3), Chase Shores (#47), Anthony Eyanson (#87), ...

    conference_draft_counts(2025)[:3]
    # SEC 107 picks, ACC 61, Big 12 57

Data Source
-----------

``src/data/draft_detail/{season}.json``, fetched by
``ncaa_bbStats.draft_detail_store`` from
https://statsapi.mlb.com/api/v1/draft/. Payloads are trimmed to the fields the
package reads; see :doc:`data_provenance`.

See Also
--------

- :doc:`mlb_draft`
- :doc:`prospects`
- :doc:`crossref`

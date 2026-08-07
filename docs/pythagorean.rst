Pythagorean Expectation
=======================

What a team's record should have been, given the runs it scored and allowed.

Overview
--------

The Pythagorean expectation estimates a team's win percentage from run
differential alone::

    expected_win_pct = R^k / (R^k + RA^k)      k = 1.83

A team well above its expectation won more close games than its run differential
justifies. Historically that gap does not repeat, so it is one of the more
useful signals for whether a season is likely to be sustained.

.. warning::

   Per-conference exponents fitted to NCAA data ship here, but they are
   **experimental and not the default**. Fitting moves the exponent between 1.45
   and 2.08, yet **not one of the 31 conference fits differs from 1.83 at
   p < 0.05** (p-values run 0.17 to 0.98). Defaulting to them would present
   noise as precision. Pass ``conference_calibrated=True`` only if you are
   specifically exploring conference effects.

Functions
---------

.. py:function:: get_pythagorean_expectation(team_name: str, year: int, division: int, exponent: float | None = None, conference_calibrated: bool = False) -> float | str

    Pythagorean expected win percentage.

    :param team_name: Team name or partial string.
    :param year: NCAA season year.
    :param division: NCAA division (1, 2, or 3).
    :param exponent: Override the exponent. Defaults to 1.83.
    :param conference_calibrated: Use the experimental conference exponent.
    :return: Expected win percentage, or an explanatory string if data is missing.

.. py:function:: compare_pythagorean_expectation(team_name: str, year: int, division: int) -> str

    Expected against actual win percentage, as a formatted summary.

    :param team_name: Team name or partial string.
    :param year: NCAA season year.
    :param division: NCAA division (1, 2, or 3).
    :return: A summary string.

.. py:function:: luck_rating(team: str, year: int, division: int = 1, *, conference_calibrated: bool = False) -> dict | None

    How much a team over- or under-performed its run differential, in win
    percentage and in games.

    :param team: Team name or substring.
    :param year: Season year.
    :param division: NCAA division (1, 2, or 3).
    :param conference_calibrated: Use the experimental conference exponent.
    :return: ``expected_win_pct``, ``actual_win_pct``, ``luck``, ``luck_wins``.

.. py:function:: luckiest_teams(year: int, division: int = 1, *, n: int = 10, conference_calibrated: bool = False) -> list[dict]

    Teams that most outperformed their run differential.

    :param year: Season year.
    :param division: NCAA division (1, 2, or 3).
    :param n: How many teams to return.
    :param conference_calibrated: Use the experimental conference exponent.
    :return: Sorted by wins above expectation.

.. py:function:: unluckiest_teams(year: int, division: int = 1, *, n: int = 10, conference_calibrated: bool = False) -> list[dict]

    Teams that most underperformed their run differential.

    :param year: Season year.
    :param division: NCAA division (1, 2, or 3).
    :param n: How many teams to return.
    :param conference_calibrated: Use the experimental conference exponent.
    :return: Sorted by wins below expectation.

.. py:function:: pythagorean_exponent(conference: str | None = None, *, default: float = 1.83) -> float

    The exponent to use, optionally fitted to a conference.

    :param conference: Conference code. If omitted or unknown, returns the default.
    :param default: Value to return when no fitted exponent applies.
    :return: The exponent.

.. py:function:: conference_exponents() -> list[dict]

    Every fitted per-conference exponent with its diagnostics, including the
    p-value and a ``significant`` flag — which reads ``"no"`` for all 31.

    :return: Sorted by exponent, largest first.

Usage
-----

.. code-block:: python

    from ncaa_bbStats import luckiest_teams, unluckiest_teams, luck_rating

    luckiest_teams(2025, n=3)
    # The Citadel   +7.4 wins above expectation
    # Clemson       +7.2
    # Rider         +7.1

    unluckiest_teams(2025, n=3)
    # UCF           -8.8 wins below expectation
    # Texas A&M     -8.6
    # Iowa          -7.3

    luck_rating("Northeastern", 2025)
    # {'expected_win_pct': 0.802, 'actual_win_pct': 0.8167, 'luck_wins': 0.88}

Data Source
-----------

Computed from ``src/data/team_stats_cache/``. Conference exponents in
``src/data/pythagorean/conference_exponents.csv``.

See Also
--------

- :doc:`team_stats`
- :doc:`crossref`

Team Stats Module
=================

The `team_stats` module provides utilities for accessing, analyzing, and visualizing college baseball team statistics across years and NCAA divisions.

Overview
--------

This module allows users to:

- Retrieve team statistics from cached JSON files.
- Aggregate statistics for a team over multiple years.
- Visualize trends in team performance using line plots.

Functions
---------

.. py:function:: get_team_stat(stat_name: str, team_name: str, year: int, division: int) -> float | int | None

    Retrieves a specific statistic for a given team from the cached data.

    :param stat_name: Key of the statistic to retrieve.
    :param team_name: Name or substring of the team.
    :param year: Year of the data.
    :param division: NCAA division number.
    :return: The value of the requested statistic, or None if not found.

.. py:function:: display_specific_team_stat(stat_name: str, search_team: str, year: int, division: int) -> None

    Prints a specific statistic for a team in a readable format.

    :param stat_name: Key of the statistic to display.
    :param search_team: Name or substring of the team.
    :param year: Year of the data.
    :param division: NCAA division number.
    :return: None. Prints the result to the console.

.. py:function:: display_team_stats(search_team: str, year: int, division: int) -> None

    Displays all available statistics for a team for a given year and division.

    :param search_team: Name or substring of the team.
    :param year: Year of the data.
    :param division: NCAA division number.
    :return: None. Prints all stats for the team.

Functions that calculate
------------------------

.. py:function:: average_all_team_stats(team_name: str, division: int, start_year: int, end_year: int) -> dict

    Calculates the average of all available statistics for a team over a range of years.

    :param team_name: Name or substring of the team.
    :param division: NCAA division number.
    :param start_year: First year in the range.
    :param end_year: Last year in the range.
    :return: Dictionary mapping stat names to their average values.

.. py:function:: average_team_stat_str(team_name: str, stat_name: str, division: int, start_year: int, end_year: int) -> str

    Calculates the average of a specific statistic (string type) for a team over a range of years.

    :param team_name: Name or substring of the team.
    :param stat_name: Key of the statistic to average.
    :param division: NCAA division number.
    :param start_year: First year in the range.
    :param end_year: Last year in the range.
    :return: Average value (str) of the specified statistic.

.. py:function:: average_team_stat_float(team_name: str, stat_name: str, division: int, start_year: int, end_year: int) -> float | None

    Calculates the average of a specific statistic (float type) for a team over a range of years.

    :param team_name: Name or substring of the team.
    :param stat_name: Key of the statistic to average.
    :param division: NCAA division number.
    :param start_year: First year in the range.
    :param end_year: Last year in the range.
    :return: Average value (float) of the specified statistic.

.. py:function:: get_pythagenpat_expectation(runs_scored: int | float, runs_allowed: int | float) -> float

    Calculates the Pythagenpat expected win percentage (using the 1.83 exponent) for a team based on runs scored and allowed.

    :param runs_scored: Total runs scored by the team.
    :param runs_allowed: Total runs allowed by the team.
    :return: Expected win percentage (float).

.. py:function:: plot_team_stat_over_years(stat_name: str, team_name: str, division: int, start_year: int, end_year: int) -> None

    Aggregates and plots a specified statistic for a team over a range of years.

    :param stat_name: Key of the statistic to plot.
    :param team_name: Name or substring of the team.
    :param division: NCAA division number.
    :param start_year: First year in the range.
    :param end_year: Last year in the range.
    :return: None. Displays a matplotlib plot if data is found.

Usage Example
-------------

.. code-block:: python

    from ncaa_bbStats import plot_team_stat_over_years

    # Plot home runs for Northeastern in Division 1 from 2010 to 2024
    plot_team_stat_over_years("home_runs", "Northeastern", 1, 2010, 2024)

Data Source
-----------

Team statistics are loaded from cached JSON files located in:

    src/data/team_stats_cache/divX/YYYY.json

where `X` is the division number and `YYYY` is the year.

See Also
--------

- :doc:`mlb_draft`
- :doc:`team_names_stats`

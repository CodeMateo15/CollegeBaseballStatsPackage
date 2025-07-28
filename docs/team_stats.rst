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
    :param team_name: Name of the team.
    :param year: Year of the data.
    :param division: NCAA division number.
    :return: The value of the requested statistic, or None if not found.

.. py:function:: display_specific_team_stat(stat_name: str, search_team: str, year: int, division: int) -> None

    Prints a specific statistic for a team in a readable format.

    :param stat_name: Key of the statistic to display.
    :param search_team: Name of the team.
    :param year: Year of the data.
    :param division: NCAA division number.
    :return: None. Prints the result to the console.

.. py:function:: display_team_stats(search_team: str, year: int, division: int) -> None

    Displays all available statistics for a team for a given year and division.

    :param search_team: Name of the team.
    :param year: Year of the data.
    :param division: NCAA division number.
    :return: None. Prints all stats for the team.

Functions that calculate
------------------------

.. py:function:: average_all_team_stats(year: int, division: int) -> dict

    Computes the average of all numeric values for each statistic across all teams.

    :param year: Year of the data.
    :param division: NCAA division number.
    :return: Dictionary mapping stat names to their average values.

.. py:function:: average_team_stat_str(stat_name: str, year: int, division: int) -> str

    Returns a string representing the average value of a given statistic across all teams for the specified year and division.

    :param stat_name: Key of the statistic to average.
    :param year: Year of the data.
    :param division: NCAA division number.
    :return: Average value (str) of the specified statistic.

.. py:function:: average_team_stat_float(stat_name: str, year: int, division: int) -> float | None

    Computes the mean of the specified statistic, if available

    :param stat_name: Key of the statistic to average.
    :param year: Year of the data.
    :param division: NCAA division number.
    :return: Average value (float) of the specified statistic.

.. py:function:: get_pythagenpat_expectation(team_name: str, year: int, division: int) -> str

    Computes Pythagenpat expected win percentage and compares it with the actual win percentage.

    :param team_name: Name of the team.
    :param year: Year of data.
    :param division: NCAA division number.
    :return: A string summary with expected and actual win percentages.

.. py:function:: plot_team_stat_over_years(stat_name: str, team_name: str, division: int, start_year: int, end_year: int)

    Plots the values of a specified statistic for a given team across a range of years in a specific NCAA division.

    :param stat_name: Key of the statistic to plot.
    :param team_name: Name of the team.
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

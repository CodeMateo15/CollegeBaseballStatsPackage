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

.. py:function:: get_team_stat(stat_name: str, team_name: str, year: int, division: int) -> float | int | None:

Retrieves a specific statistic for a given team from the cached data.

**Parameters:**
    - `team_name` (str): Name or substring of the team.
    - `stat_name` (str): Key of the statistic to retrieve.
    - `division` (int): NCAA division number.
    - `year` (int): Year of the data.

**Returns:**
    - The value of the requested statistic, or None if not found.


.. py:function:: display_specific_team_stat(stat_name: str, search_team: str, year: int, division: int) -> None:

Prints a specific statistic for a team in a readable format.

**Parameters:**
    - `team_name` (str): Name or substring of the team.
    - `stat_name` (str): Key of the statistic to display.
    - `division` (int): NCAA division number.
    - `year` (int): Year of the data.

**Returns:**
    - None. Prints the result to the console.


.. py:function:: display_team_stats(search_team: str, year: int, division: int) -> None:

Displays all available statistics for a team for a given year and division.

**Parameters:**
    - `team_name` (str): Name or substring of the team.
    - `division` (int): NCAA division number.
    - `year` (int): Year of the data.

**Returns:**
    - None. Prints all stats for the team.


Functions that calculate
--------------------

.. py:function:: average_all_team_stats(year: int, division: int) -> dict:

Calculates the average of all available statistics for a team over a range of years.

**Parameters:**
    - `team_name` (str): Name or substring of the team.
    - `division` (int): NCAA division number.
    - `start_year` (int): First year in the range.
    - `end_year` (int): Last year in the range.

**Returns:**
    - Dictionary mapping stat names to their average values.


.. py:function:: average_team_stat_str(stat_name: str, year: int, division: int) -> str:

Calculates the average of a specific statistic (string type) for a team over a range of years.

**Parameters:**
    - `team_name` (str): Name or substring of the team.
    - `stat_name` (str): Key of the statistic to average.
    - `division` (int): NCAA division number.
    - `start_year` (int): First year in the range.
    - `end_year` (int): Last year in the range.

**Returns:**
    - Average value (str) of the specified statistic.


.. py:function:: average_team_stat_float(stat_name: str, year: int, division: int) -> float | None:

Calculates the average of a specific statistic (float type) for a team over a range of years.

**Parameters:**
    - `team_name` (str): Name or substring of the team.
    - `stat_name` (str): Key of the statistic to average.
    - `division` (int): NCAA division number.
    - `start_year` (int): First year in the range.
    - `end_year` (int): Last year in the range.

**Returns:**
    - Average value (float) of the specified statistic.


.. py:function:: get_pythagenpat_expectation(team_name: str, year: int, division: int) -> str:

Calculates the Pythagenpat expected win percentage (using the 1.83 exponent) for a team based on runs scored and allowed.

**Parameters:**
    - `runs_scored` (int or float): Total runs scored by the team.
    - `runs_allowed` (int or float): Total runs allowed by the team.

**Returns:**
    - Expected win percentage (float).


.. py:function:: plot_team_stat_over_years(stat_name: str, team_name: str, division: int, start_year: int, end_year:

Aggregates and plots a specified statistic for a team over a range of years.

**Parameters:**
    - `stat_name` (str): Key of the statistic to plot.
    - `team_name` (str): Name or substring of the team.
    - `division` (int): NCAA division number.
    - `start_year` (int): First year in the range.
    - `end_year` (int): Last year in the range.

**Returns:**
    - None. Displays a matplotlib plot if data is found.

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

- :doc:`draft_stats`

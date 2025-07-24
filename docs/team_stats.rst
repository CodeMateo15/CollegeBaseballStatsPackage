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

.. autofunction:: get_team_stat_over_years

    Retrieves the values of a specified statistic for a given team across a range of years and division.

    **Parameters:**
        - `stat_name` (str): The key of the statistic to retrieve (e.g., ``home_runs``, ``W``, ``R (Batting)``).
        - `team_name` (str): Substring to match against team names (case-insensitive).
        - `division` (int): NCAA division number (1, 2, or 3).
        - `start_year` (int): The first year in the range.
        - `end_year` (int): The last year in the range.

    **Returns:**
        - `years` (list of int): Years for which data was found.
        - `stat_values` (list): Corresponding stat values.

.. autofunction:: plot_team_stat_over_years

    Aggregates and plots a specified statistic for a team over a range of years and division.

    **Parameters:**
        - `stat_name` (str): The key of the statistic to plot.
        - `team_name` (str): Substring to match against team names.
        - `division` (int): NCAA division number.
        - `start_year` (int): The first year in the range.
        - `end_year` (int): The last year in the range.

    **Returns:**
        - None. Displays a matplotlib plot if data is found, otherwise prints a message.

Usage Example
-------------

.. code-block:: python

    from ncaa_bbStats.team_stats import plot_team_stat_over_years

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
- :doc:`average`

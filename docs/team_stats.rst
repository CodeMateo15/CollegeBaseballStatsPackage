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

get_team_stat
~~~~~~~~~~~~~
Retrieves a specific statistic for a given team from the cached data.

**Parameters:**
    - `team_name` (str): Name or substring of the team.
    - `stat_name` (str): Key of the statistic to retrieve.
    - `division` (int): NCAA division number.
    - `year` (int): Year of the data.

**Returns:**
    - The value of the requested statistic, or None if not found.

display_specific_team_stat
~~~~~~~~~~~~~~~~~~~~~~~~~~
Prints a specific statistic for a team in a readable format.

**Parameters:**
    - `team_name` (str): Name or substring of the team.
    - `stat_name` (str): Key of the statistic to display.
    - `division` (int): NCAA division number.
    - `year` (int): Year of the data.

**Returns:**
    - None. Prints the result to the console.

display_team_stats
~~~~~~~~~~~~~~~~~~
Displays all available statistics for a team for a given year and division.

**Parameters:**
    - `team_name` (str): Name or substring of the team.
    - `division` (int): NCAA division number.
    - `year` (int): Year of the data.

**Returns:**
    - None. Prints all stats for the team.

get_pythagenpat_expectation
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Calculates the Pythagenpat expected win percentage for a team based on runs scored and allowed.

**Parameters:**
    - `runs_scored` (int or float): Total runs scored by the team.
    - `runs_allowed` (int or float): Total runs allowed by the team.

**Returns:**
    - Expected win percentage (float).

plot_team_stat_over_years
~~~~~~~~~~~~~~~~~~~~~~~~~
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
- :doc:`average`

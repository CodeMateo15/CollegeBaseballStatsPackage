MLB Draft Team/School Names
=====================================

This file lists all unique school names found under the "Drafted From" and "Drafted By" field in the MLB draft data cache.
These schools have been cleaned by removing any conference or league information (ex. text inside parentheses).

Each entry includes:

- A unique `school_id` and 'team_id'
- The cleaned `school_name` and 'team_name'

Download
--------

You can download the CSV file here:

:download:`drafted_by_teams.csv <_static/data/mlb_team_names/drafted_by_teams.csv>`


:download:`drafted_from_schools.csv <_static/data/mlb_team_names/drafted_from_schools.csv>`


.. note::

   For By Teams, you must use the team_name (ex. Atlanta Braves or Boston Red Sox). You can also just use Braves or Red Sox, without the location the team is based on. team_id has not been implemented yet.

.. note::

   For From Schools, you must use the school_name (ex. Northeastern University or Ohio State). school_id has not been implemented yet.

See Also
--------

- :doc:`mlb_draft`

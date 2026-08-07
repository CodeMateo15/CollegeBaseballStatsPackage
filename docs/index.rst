===========================================
ncaa_bbStats documentation
===========================================

**ncaa_bbStats** is an open-source NCAA baseball analysis package for Python.

It covers NCAA Division I, II, and III team statistics (2002-2026), player
statistics (2021-2025), MLB Draft history (1965-2025), draft detail with
signing bonuses and slot values (2021-2026), RPI and schedule strength, program
finances, and a draft-prediction model with scouting reports.

Every dataset is cached in the package, so it works offline; scraping is opt-in.
A canonical team registry reconciles the different ways each source spells
school names, so all of it joins.

.. code-block:: python

   from ncaa_bbStats import team_profile, leaderboard, scouting_report

   team_profile("Tennessee", 2024)          # every dataset, one call
   leaderboard("era", stat_type="pitching", year=2025, min_ip=60)
   print(scouting_report("Kade Anderson", 2025))

.. note::

   This project is under active development.

.. note::

   Where each dataset comes from, on what terms, and its known limitations are
   recorded in :doc:`data_provenance`.


.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   install

.. toctree::
   :maxdepth: 2
   :caption: Team Stats

   team_stats
   team_registry
   season_stats
   rpi
   program_finance
   pythagorean

.. toctree::
   :maxdepth: 2
   :caption: Player Stats

   player_stats
   advanced_stats
   leaderboards
   player_reference

.. toctree::
   :maxdepth: 2
   :caption: Draft

   mlb_draft
   draft_detail
   prospects
   scouting

.. toctree::
   :maxdepth: 2
   :caption: Cross-Dataset

   crossref

.. toctree::
   :maxdepth: 1
   :caption: Reference

   team_names_stats
   team_names_mlb
   player_names
   regenerating
   data_provenance

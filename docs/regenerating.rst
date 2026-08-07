Regenerating the Data
=====================

Every dataset ships pre-built, so none of this is needed to use the package.
This is for extending coverage to a new season, or verifying that the shipped
data really is what the builders produce.

None of these modules ship in the wheel's import path as user API; they are
scripts. Importing any of them has no side effects.

Overview
--------

===================================  ===============================  ====================
Builder                              Produces                         Reproducible?
===================================  ===============================  ====================
``ncaa_bbStats.team_store``          ``data/team_stats_cache/``       network
``ncaa_bbStats.draft_store``         ``data/mlb_draft_cache/``        network
``ncaa_bbStats.draft_detail_store``  ``data/draft_detail/``           network
``ncaa_bbStats.rpi_store``           ``data/rpi/``                    from a local export
``ncaa_bbStats.prospect_store``      ``data/prospects/``              from a local export
``ncaa_bbStats.program_store``       ``data/program_finance/``        from a local download
``ncaa_bbStats.team_names_store``    ``data/team_names_stats/``       **yes**
``ncaa_bbStats.model_store``         ``data/models/``                 **yes**
``tools/build_league_constants.py``  ``data/league_constants/``       **yes**
``tools/build_team_registry.py``     ``data/registry/``               **yes**
``tools/build_player_registry.py``   ``data/player_registry/``        **yes**
``docs/make_static_data.py``         ``docs/_static/data/``           **yes**
===================================  ===============================  ====================

"Reproducible" means the builder is a pure function of data already in the
package, so a fresh run must reproduce the committed output byte for byte —
``tests/`` asserts exactly that for the league constants and the team registry.

Order matters
-------------

Later builders read what earlier ones write.

.. code-block:: console

   # 1. Raw sources
   python -m ncaa_bbStats.team_store --years 2027
   python -m ncaa_bbStats.draft_detail_store --years 2027

   # 2. Derived from the team cache
   python tools/build_league_constants.py

   # 3. Identity, which everything downstream joins through
   python tools/build_team_registry.py
   python tools/build_player_registry.py

   # 4. Datasets that resolve team names through the registry
   python -m ncaa_bbStats.rpi_store --from-dir path/to/rpi
   python -m ncaa_bbStats.prospect_store --from-dir path/to/prospects
   python -m ncaa_bbStats.program_store --eada-dir "path/to/EADA Data"

   # 5. Models, which read all of the above
   python -m ncaa_bbStats.model_store

   # 6. Docs downloads, then verify
   python docs/make_static_data.py
   python -m pytest tests/ -q

Adding a season
---------------

``team_store`` needs the NCAA's ranking-period id for the new year, in
``RANKING_PERIODS`` in ``ncaa_bbStats/team_stats.py``, and each stat's
``valid_years`` range extended. Everything after that follows the sequence above.

Notes on individual builders
----------------------------

**team_store** scrapes stats.ncaa.org, which sits behind Akamai Bot Manager and
returns 403 to plain HTTP/1.1 clients regardless of headers; the scraper uses
``curl_cffi`` to negotiate HTTP/2 with a real browser TLS fingerprint. It will
not overwrite a good cache file when every fetch for a season fails.

**draft_detail_store** trims the API payload to the fields the package reads,
which takes six seasons from 11.6 MB to 1.9 MB. It drops ``blurb`` — MLB
Pipeline's editorial prose, and the one field here with a real authorship claim
— while keeping the scouting-report URL, so the material stays reachable at the
source.

**rpi_store** refuses to write if any team name fails to resolve, rather than
leaving rows with empty team columns that read as "no data". If it stops, add
the spelling to ``tools/team_aliases_manual.csv`` and rebuild the registry.

**program_store** reads the EADA workbooks from
https://ope.ed.gov/athletics/#/datafile/list — take the combined data file for
each academic year, which unpacks to ``EADA_<YYYY>.xlsx``. They are about 100 MB
each and are never shipped; only the twelve derived features are.

**build_team_registry** refuses to write if any alias resolves to more than one
program. That check is what caught eleven acronyms pointing at the wrong school
in the source name table.

**build_player_registry** runs in strict mode by default. ``--permissive``
enables an extra join rule that raises recall and lowers precision; prefer
strict, since a false join fabricates a season count and a birth year and hands
the eligibility engine a confidently wrong answer.

**model_store** needs the ``model`` extra. It writes both boosters, a manifest
recording the exact feature order, and the training matrix — so the models can be
refitted from the wheel alone.

Private inputs
--------------

Anything not redistributable lives in ``private/``, which is gitignored and never
packaged. See ``tools/README.md`` and :doc:`data_provenance`.

See Also
--------

- :doc:`data_provenance`
- :doc:`team_registry`
- :doc:`scouting`

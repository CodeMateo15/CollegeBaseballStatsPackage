============
Install
============

.. code-block:: console

   pip install ncaa_bbStats

Requires Python 3.10 or later.

That gives you every dataset and every read function. All data is cached in the
package, so nothing here needs a network connection.

Optional extras
---------------

.. code-block:: console

   pip install "ncaa_bbStats[model]"     # draft predictions and scouting reports
   pip install "ncaa_bbStats[explain]"   # the above, plus SHAP explanations
   pip install "ncaa_bbStats[scrape]"    # re-scrape the sources yourself
   pip install "ncaa_bbStats[all]"       # everything

============  ===================================  ==============================
Extra         Pulls in                             Needed for
============  ===================================  ==============================
``model``     xgboost                              :doc:`scouting`
``explain``   xgboost, shap                        SHAP attributions
``scrape``    requests, beautifulsoup4, curl_cffi  the ``*_store`` modules
============  ===================================  ==============================

Nothing in the base install imports these, so ``import ncaa_bbStats`` stays fast
whether or not they are present. Calling a function that needs one raises
``MissingDependencyError`` naming the exact command to run, and
:func:`explain_prediction` falls back to a gain-based explanation when SHAP is
absent rather than failing.

Examples
--------

The repository carries runnable notebooks covering every public function, with
outputs saved so they read without executing anything:

.. code-block:: console

   git clone https://github.com/CodeMateo15/CollegeBaseballStatsPackage
   pip install -e ".[all]" jupyter
   jupyter lab notebooks/

Quick check
-----------

.. code-block:: python

   import ncaa_bbStats as nb

   nb.list_all_teams(2025, 1)[:3]
   nb.get_team_stat("HR", "Northeastern", 2025, 1)
   nb.leaderboard("era", stat_type="pitching", year=2025, min_ip=60, n=5)

.. note::

   This project is under active development. See
   `PyPI <https://pypi.org/project/ncaa-bbStats/>`_ for release history, and
   :doc:`data_provenance` for where each dataset comes from.

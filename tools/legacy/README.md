# Legacy data-munging scripts

These were written ad hoc and lived inside `src/data/`, beside the data they
operated on. That meant setuptools discovered them as importable modules and
shipped them inside every wheel. They are parked here until the logic they
carry is folded into the maintained builders under `tools/`, at which point they
should be deleted (git history keeps them).

None of them are maintained, none are packaged, and none should be run against
the current tree without reading them first. Known problems:

- All use hardcoded relative filenames and must be run from a specific directory.
- `player_stats_cache_batting_clean.py` reads `pitching_qualified.csv` and
  `player_stats_cache_pitching_clean.py` reads `pitching_noMin.csv` — they were
  copy-pasted and the paths were never corrected. This is the likely origin of
  the clobber in commit `a4320ec` that left `pitching_qualified.csv` byte-identical
  to `pitching_noMin.csv`.
- `team_names_stats_rename.py` handles Division I only and falls back to
  `difflib.get_close_matches(cutoff=0.5)`, which is loose enough to produce wrong
  matches silently.

| Script | Superseded by |
| --- | --- |
| `player_stats_cache_*_{clean,rename}.py` | `tools/migrate_fg_to_public.py` |
| `team_names_stats_{rename,merge,duplicates,unused}.py` | `tools/build_team_registry.py` |
| `mlb_team_names_unused.py` | `tools/build_team_registry.py` |

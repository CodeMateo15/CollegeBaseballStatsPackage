# Data builders

Scripts that regenerate the packaged data. They are committed but not packaged —
nothing here ships in the wheel, and the package never imports from `tools/`.

Run from the repository root.

| Script | Reads | Writes | Reproducible? |
| --- | --- | --- | --- |
| `build_league_constants.py` | `src/data/team_stats_cache/` | `src/data/league_constants/` | **Yes.** Pure function of public NCAA data; `tests/test_advanced_stats.py` asserts a fresh build is byte-identical. |
| `migrate_fg_to_public.py` | `private/fg/` | `src/data/player_stats_cache/` | No — needs the private inputs. Input hashes are recorded in the output manifest. |

## `private/`

Gitignored, never packaged. Holds non-redistributable inputs used to regenerate
the public data. See `DATA_PROVENANCE.md`.

To populate it:

```bash
mkdir -p private/fg
# The three current exports, plus the qualified pitching file, which was
# overwritten in commit a4320ec and survives only in git history:
git show 7afa3b1:src/data/player_stats_cache/pitching/pitching_qualified.csv \
  > private/fg/pitching_qualified.csv
```

The recovered file is verifiable: 5,642 rows, 40 columns, and its
`(name, team, age, year)` tuples match the old
`docs/_static/data/player_stats/pitching_qualifiedDOC.csv` snapshot row for row.

Do not `git checkout` those files into the working tree — that re-commits data
the package does not redistribute.

## Order of operations

```bash
python tools/build_league_constants.py      # 1. public, always safe to rerun
python tools/migrate_fg_to_public.py --check  # 2. review what changes
python tools/migrate_fg_to_public.py          # 3. write
python docs/make_static_data.py               # 4. refresh docs downloads
python -m pytest tests/ -q                    # 5. verify
```

`legacy/` holds the ad-hoc scripts these replaced; see its README.

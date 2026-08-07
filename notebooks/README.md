# Notebooks

Runnable demonstrations of every public function, with outputs saved so they
read without executing anything.

These are **examples, not tests**. The test suite is `tests/`, run with
`pytest`. This folder used to be called `test/`, which was confusing once a real
`tests/` existed alongside it.

| Notebook | Covers |
| --- | --- |
| `01_team_stats.ipynb` | Team statistics, the team registry, Pythagorean expectation and luck ratings |
| `02_player_stats.ipynb` | Player seasons, the derived advanced metrics, leaderboards |
| `03_draft.ipynb` | Draft history 1965–2025, draft detail with bonuses 2021–2026, prospect rankings |
| `04_rpi_and_program_finance.ipynb` | RPI, schedule strength, quadrant records, EADA program finances |
| `05_cross_dataset.ipynb` | Questions needing several datasets at once |
| `06_scouting.ipynb` | Draft predictions, explanations, scouting reports |

All 103 public functions appear across the six. `tests/test_notebooks.py` fails
if a function is added to the public API without an example.

## Running them

```bash
pip install -e ".[all]" jupyter
jupyter lab notebooks/
```

Only `06_scouting.ipynb` needs an optional extra (`model` for predictions,
`explain` for SHAP attributions). The other five run on the base install, with
no network — every dataset is cached in the package.

## Regenerating

The `.ipynb` files are **generated**, not hand-edited. Edit
`build_notebooks.py` and re-run it:

```bash
python notebooks/build_notebooks.py            # write and execute
python notebooks/build_notebooks.py --no-exec  # write only
```

It refuses to claim success if any public function is undemonstrated, and stops
on the first cell that raises. Generating them means the whole set can be
re-run against a new release without anyone reconciling a hundred cells by
hand — and the saved outputs are then guaranteed to match the shipped code.

## Legacy

`_legacy_*.ipynb` are the original three notebooks, kept for reference. They
predate the 1.2.0 rewrite — and all three still execute unchanged against it,
which is the clearest evidence that the public API stayed backward compatible
even though the player cache changed shape underneath. They cover a fraction of
the API, so prefer the numbered notebooks.

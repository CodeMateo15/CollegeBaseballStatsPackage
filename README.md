# ncaa_bbStats (AKA CollegeBaseballStatsPackage)

**ncaa_bbStats** is an open-source Python package for retrieving, parsing, and
analyzing college baseball data: NCAA Division I, II, and III team statistics
(2002–2026), player statistics (2021–2026), MLB Draft history (1965–2025),
draft detail with signing bonuses (2021–2026), RPI and schedule strength,
program finances, and a draft-prediction model with scouting reports.

Built for analysts, developers, and fans. Everything is cached locally, so it
works offline; scraping is opt-in.

The draft model in this package powers a public site where you can browse a
board, look up a player, or score a stat line of your own:
**https://codemateo15-ncaa-draft-app.share.connect.posit.cloud/**
([source](https://github.com/CodeMateo15/ncaa-draft-app))

> **Note**
> This project is under active development.

---

## Documentation
Documentation: <a href="https://collegebaseballstatspackage.readthedocs.io/en/latest/index.html" target="_blank">ncaa_bbStats on ReadTheDocs</a>

PyPI: <a href="https://pypi.org/project/ncaa-bbStats/" target="_blank">ncaa-bbStats</a>

Data sources and terms: [DATA_PROVENANCE.md](DATA_PROVENANCE.md)

---

## Install

```bash
pip install ncaa_bbStats                 # everything except predictions
pip install "ncaa_bbStats[model]"        # + draft predictions
pip install "ncaa_bbStats[explain]"      # + SHAP explanations
pip install "ncaa_bbStats[scrape]"       # + re-scraping the sources yourself
```

Requires Python 3.10 or later.

---

## A tour

```python
from ncaa_bbStats import (
    team_profile, leaderboard, scouting_report, resolve_team, luckiest_teams,
)

# Everything about one program in one season, across every dataset
p = team_profile("Tennessee", 2024)
p["record"]            # 60-13, .822
p["rpi"]["rpi_rank"]   # 1
p["draft"]["picks"]    # 8
p["pythagorean"]       # expected .807 against an actual .822

# Leaderboards that sort the right way round
leaderboard("era", stat_type="pitching", year=2025, min_ip=60, n=10)
leaderboard("cwrc+", year=2025, conference="SEC", n=10)
leaderboard("hr", per="career", qualifier="noMin", n=5)

# Every source spells schools differently; one id resolves them all
resolve_team("Eastern Ill.") == resolve_team("EIU") == resolve_team("Eastern Illinois")

# Who won more than their run differential deserved?
luckiest_teams(2025, n=5)

# A scouting report
print(scouting_report("Kade Anderson", 2025))
```

---

## What's in it

| Dataset | Coverage |
| --- | --- |
| NCAA team statistics | 2002–2026, Divisions I–III |
| Player statistics | 2021–2026, Division I |
| MLB Draft history | 1965–2025, 69,169 picks |
| MLB Draft detail (bonuses, slots, biography) | 2021–2026, 3,685 picks |
| RPI, strength of schedule, quadrant records | 2021–2026, Division I |
| Program finances ([EADA](https://ope.ed.gov/athletics/#/datafile/list)) | 2021–2025, carried forward to 2026 |
| Draft prospect rankings | 2021–2026 |
| Team registry | 1,023 programs |
| Player registry | 27,283 players |

---

## Modules

### Team stats
`get_team_stat`, `display_team_stats`, `display_specific_team_stat`,
`list_all_teams`, `plot_team_stat_over_years`, `average_all_team_stats`,
`average_team_stat_str`, `average_team_stat_float`

### Team registry
One canonical `team_id` per program, so datasets that spell schools differently
can be joined. Keyed on the federal IPEDS unitid where known, which survives
rebrands — Dixie State and Utah Tech share an id. Division is a per-season
attribute, not part of identity.

`resolve_team`, `resolve_team_verbose`, `team_info`, `team_aliases`,
`team_seasons`, `team_division`, `team_conference`, `list_teams`,
`list_conferences`, `crosswalk`

### Player stats
`list_players`, `list_batters`, `list_pitchers`, `player_seasons`,
`batting_stat`, `pitching_stat`, `get_player_rows`, `load_player_frame`,
`list_available_years`

The cache stores counting statistics only. Every rate and advanced statistic is
computed when you read it, from those counts plus league constants this package
derives from its own NCAA team data — so they can never fall out of step.

### Advanced stats
`cwoba`, `cwraa`, `cwrc`, `cwrc_plus`, `cwsb`, `cspd`, `cfip`, `clob_pct`,
`league_constants`, `seasons_with_constants`

College-calibrated analogues of the familiar sabermetric statistics, built the
same way but with league constants regressed from NCAA play rather than borrowed
from elsewhere. See [DATA_PROVENANCE.md](DATA_PROVENANCE.md) for the method and
measured correlations.

### Leaderboards
`leaderboard`, `stat_direction`, `qualification_rules`

Takes the sort direction from the statistic, so a top-ERA list contains good
pitchers. Supports playing-time floors, team and conference filters, and career
aggregation that rebuilds rates from summed components.

### Draft
`parse_mlb_draft`, `get_drafted_players_mlb`, `get_drafted_players_college`,
`print_draft_picks_mlb`, `print_draft_picks_college` (1965–2025)

`draft_pick`, `draft_class`, `draft_history`, `slot_value`, `signing_bonus`,
`bonus_vs_slot`, `overslot_picks`, `biggest_bonuses`, `draft_demographics`,
`conference_draft_counts`, `state_pipeline` (2021–2026, with bonuses and slots)

`prospect_rank`, `prospect_board`, `prospect_vs_actual`, `biggest_draft_risers`,
`biggest_draft_fallers`

### RPI and program finances
`rpi_rank`, `strength_of_schedule`, `rpi_table`, `rpi_record`,
`quadrant_record`, `home_road_neutral`, `nonconference_profile`,
`rpi_over_years`, `best_wins`

`program_finance`, `budget_percentile`, `roster_size`, `coaching_staff_size`,
`richest_programs`, `conference_spending`, `finance_vs_rpi`

### Pythagorean expectation
`get_pythagorean_expectation`, `compare_pythagorean_expectation`,
`luck_rating`, `luckiest_teams`, `unluckiest_teams`, `pythagorean_exponent`,
`conference_exponents`

### Cross-dataset
`team_profile`, `player_profile`, `draft_yield`, `dollars_per_draft_pick`,
`conference_report`, `pipeline`, `compare_teams`

### Scouting and draft prediction
`scouting_report`, `predict_draft_probability`, `predict_draft_order`,
`draft_board`, `explain_prediction`, `predict_from_stats`, `is_draft_eligible`,
`model_card`

Two models: whether a player-season leads to being drafted (PR-AUC 0.708,
ROC-AUC 0.962 on a held-out 2025) and where a drafted player falls in their
class (Spearman 0.644). Explanations come from SHAP where installed, with a
gain-based fallback that says which it used.

Read `model_card()` before quoting any of it — it carries the limitations,
including that Stage 1 precision depends on the base rate you apply it to, that
eligibility is inferred rather than looked up, and that order predictions have a
mean absolute error of 76 places, so they separate tiers rather than picks.

```python
from ncaa_bbStats import predict_from_stats

result = predict_from_stats(
    "pitcher", age=21,
    stats={"era": 2.40, "so": 130, "bb": 25, "ip": 95.0},
    team="LSU", season=2025,
)
print(result["report"])
result["confidence"]   # 'low' -- reports how much had to be imputed
```

---

## Reference

- <a href="https://collegebaseballstatspackage.readthedocs.io/en/latest/season_stats.html" target="_blank">Team stat abbreviations</a>
- <a href="https://collegebaseballstatspackage.readthedocs.io/en/latest/player_reference.html" target="_blank">Player stat abbreviations</a>
- <a href="https://collegebaseballstatspackage.readthedocs.io/en/latest/team_registry.html" target="_blank">Team registry</a> — how team names resolve
- <a href="https://collegebaseballstatspackage.readthedocs.io/en/latest/data_provenance.html" target="_blank">Data provenance</a> — sources, terms, and known limitations

---

## Examples

Runnable notebooks covering every public function, with outputs saved so they
read without executing anything, live in [`notebooks/`](notebooks/):

```bash
pip install -e ".[all]" jupyter
jupyter lab notebooks/
```

## Regenerating the data

Builders live in `tools/` and the `*_store` modules; none of them ship in the
wheel. See [tools/README.md](tools/README.md).

```bash
python -m ncaa_bbStats.team_store --years 2026    # scrape NCAA team stats
python tools/build_league_constants.py            # refit the run values
python tools/build_team_registry.py               # rebuild the registry
python -m ncaa_bbStats.model_store                # retrain the draft models
python -m pytest tests/ -q
```

---

## Planned

- Player statistics re-sourced directly from stats.ncaa.org, which would remove
  the last third-party dependency in the data — see
  [DATA_PROVENANCE.md](DATA_PROVENANCE.md)
- IPEDS identifiers backfilled for Division II and III programs
- Team game results with win-loss tracking
- Park factors, which currently limit `cwrc_plus`

Found a bug or want a feature? Open an [issue](https://github.com/CodeMateo15/CollegeBaseballStatsPackage/issues).

## Support
Star this repo and share to help support!
[![GitHub stars](https://img.shields.io/github/stars/CodeMateo15/CollegeBaseballStatsPackage.svg?style=social&label=Star)](https://github.com/CodeMateo15/CollegeBaseballStatsPackage)

## Contact
Mateo Biggs, mateojohn2024@gmail.com

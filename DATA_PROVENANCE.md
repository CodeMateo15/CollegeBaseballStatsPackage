# Data provenance

Every dataset shipped in `ncaa_bbStats`, where it came from, and on what basis
it is redistributed. If you are adding a dataset, add a row here first.

## Datasets

| Dataset | Path | Source | Terms | Coverage |
| --- | --- | --- | --- | --- |
| NCAA team statistics | `src/data/team_stats_cache/div{1,2,3}/{year}.json` | [stats.ncaa.org](https://stats.ncaa.org) national rankings tables, scraped by `ncaa_bbStats.team_stats` | Official NCAA statistics; factual game records | 2002–2026, Divisions I–III |
| MLB draft history | `src/data/mlb_draft_cache/*.json` | [Baseball Almanac](https://www.baseball-almanac.com), scraped by `ncaa_bbStats.draft_stats` | Factual draft records | 1965–2025, 69,169 picks |
| Player statistics | `src/data/player_stats_cache/{batting,pitching}/*.csv` | See **FanGraphs** below | Counting statistics only; see below | 2021–2025, Division I |
| Team / school name tables | `src/data/team_names_stats/`, `src/data/mlb_team_names/` | Derived from the caches above by `ncaa_bbStats.team_names_store` | Package's own work | — |

Facts about sporting events — who played, how many hits they got — are not
themselves copyrightable in the United States (*Feist Publications v. Rural
Telephone Service*, 499 U.S. 340 (1991)). What is protectable is a compiler's
original selection, arrangement, and derived analytics. That distinction is what
draws the line below.

## FanGraphs

The player statistics in this package originate from FanGraphs' college
leaderboards, which sit behind a paid FanGraphs Membership. **FanGraphs' terms of
use do not permit redistribution of their bulk leaderboard data**, and the
research repository these files came from gitignores them for exactly that reason.

Two categories were removed in version 1.2.0:

**FanGraphs-derived metrics.** `wRC+`, `wOBA`, `wRAA`, `wRC`, `wSB`, `Spd`,
`FIP`, `E-F`, and `LOB%` all depend on FanGraphs' own NCAA linear weights, league
constants, and park factors. Those are FanGraphs' analytical product, not facts.
They are replaced by package-original equivalents (below).

**FanGraphs identifiers.** FanGraphs' `playerid` (values like `29547` or
`sa3025257`) is their internal key. It is replaced by a package-owned
`player_id`. The `mlbamid` column is re-sourced from the public MLB Stats API
rather than inherited from the FanGraphs export.

**What was kept, and the honest caveat.** Raw counting statistics — games,
at-bats, hits, doubles, home runs, walks, strikeouts, innings pitched, earned
runs — are records of what happened on the field. They are NCAA's facts, and no
compiler acquires exclusive rights in them by publishing them. They are retained.

But their *provenance in this package* is still a FanGraphs export, even though
the underlying facts are not FanGraphs'. Re-deriving them directly from
stats.ncaa.org individual-player pages is planned, and would remove the
dependency entirely. `ncaa_bbStats.team_stats` already handles that site's bot
protection. Until that lands, this section is the accurate description of where
these numbers came from.

**Version history.** Releases 1.0.x and 1.1.0 did not include
`src/data/player_stats_cache` — `MANIFEST.in` never listed it — so no published
wheel or source distribution contains FanGraphs data. The files were, however,
committed to the public git repository, and remain reachable in history at
commits `c418135`, `8c3d55b`, `7afa3b1`, and `a4320ec`. History has not been
rewritten.

## Package-original metrics

Replacements for the removed FanGraphs metrics, computed from public counting
statistics using linear weights this package derives from its own NCAA team-stats
cache. Full formulas and the regression method are in
`docs/advanced_stats.rst`; constants ship in `src/data/league_constants/`.

Correlation against the FanGraphs columns they replace (2021–2025, Division I),
published so the derivation can be judged as independent work rather than a
repackaging:

| Metric | Replaces | Pearson r |
| --- | --- | --- |
| `cwoba` | `wOBA` | 0.9928 |
| `cfip` | `FIP` | 0.9964 |
| `clob_pct` | `LOB%` | 0.9911 |
| `cwrc_plus` | `wRC+` | 0.9689 |
| `cspd` | `Spd` | 0.910 |

### Known limitations

- **No park factors.** `cwrc_plus` assumes a park factor of 1.0 for every
  program. NCAA park data is not publicly available; deriving it would require
  game logs. Hitters at extreme-altitude programs (Mountain West, RMAC) are
  therefore flattered relative to a park-adjusted figure, and magnitudes are not
  comparable to FanGraphs' `wRC+`.
- **Batting-side proxies.** The team cache has no home-runs-allowed field in any
  season, and no `BB (Pitching)` before 2011 (2012 for Division III). League
  totals from the batting side stand in. Measured closure error is 0.4–2.1%.
- **No weights before 2008.** Seasons 2002–2007 record only at-bats, hits, and
  runs, which is not enough to fit event weights. Advanced metrics return `None`
  for those seasons rather than a fabricated value.
- **Division II has no sacrifice-hit data** in any season. This does not affect
  the metrics: the plate-appearance denominator is `AB + BB + HBP + SF`, which
  excludes sacrifice hits by construction.
- **`cspd` is informational.** At r = 0.910 it is the weakest of the set and its
  calibration is arbitrary. All of its inputs are retained in full, so prefer
  those for modelling.

## Player identity

`player_id` is assigned by this package, not inherited from any source. It is
stable within a major version. Splits and merges may occur in minor releases and
are always recorded in `src/data/player_registry/player_id_aliases.csv` with a
reason; a retired id is never reassigned to a different person. Use
`resolve_player_id()` to follow an alias chain. Ids are never renumbered in a
patch release.

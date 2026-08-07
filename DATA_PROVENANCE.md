# Data provenance

Every dataset shipped in `ncaa_bbStats`, where it came from, and on what basis
it is redistributed. If you are adding a dataset, add a row here first.

## Datasets

| Dataset | Path | Source | Terms | Coverage |
| --- | --- | --- | --- | --- |
| NCAA team statistics | `src/data/team_stats_cache/div{1,2,3}/{year}.json` | [stats.ncaa.org](https://stats.ncaa.org) national rankings tables, scraped by `ncaa_bbStats.team_stats` | Official NCAA statistics; factual game records | 2002–2026, Divisions I–III |
| MLB draft history | `src/data/mlb_draft_cache/*.json` | [Baseball Almanac](https://www.baseball-almanac.com), scraped by `ncaa_bbStats.draft_stats` | Factual draft records | 1965–2025, 69,169 picks |
| Player statistics | `src/data/player_stats_cache/{batting,pitching}/*.csv` | See **FanGraphs** below | Counting statistics only; see below | 2021–2025, Division I |
| League constants | `src/data/league_constants/*.csv` | Regressed from `team_stats_cache` by `tools/build_league_constants.py` | Package's own work | 2008–2026 (D-III from 2009) |
| Team registry | `src/data/registry/*.csv` | Built from the caches above plus IPEDS unitids by `tools/build_team_registry.py` | Package's own work; IPEDS identifiers are U.S. federal public domain | 1,023 programs, 2002–2026 |
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

Run values are fitted per season and division by weighted least squares over
team-season totals (R² 0.96–0.98 on runs scored, RMSE about 16 runs against
seasons averaging 300), then shrunk toward the division's pooled estimate. The
shrinkage matters: the season-to-season spread of the raw coefficients is about
the same size as their standard errors, so most of the movement is sampling
noise. Home-run and hit-by-pitch weights shrink fully to the pooled value;
singles and walks retain roughly half their season-specific estimate.

The hit-type weights are then projected onto the ordering that physics requires
(1B ≤ 2B ≤ 3B ≤ HR) by inverse-variance-weighted isotonic regression. Without
it, 34 of 55 division-seasons place the triple above the home run — an artifact
of triples occurring in well under 1% of plate appearances, which leaves their
coefficient absorbing rally context. Correlations below are unaffected by the
projection; it only repairs impossible orderings.

Measured correlation against the metrics they replace, over the qualified
Division I population (11,529 batting and 5,642 pitching seasons, 2021–2025).
Published so the derivation can be judged as independent work rather than a
repackaging:

| Metric | Replaces | Pearson r | Spearman |
| --- | --- | --- | --- |
| `clob_pct` | `LOB%` | 1.0000 | 1.0000 |
| `cwrc` | `wRC` | 0.9961 | 0.9962 |
| `cwoba` | `wOBA` | 0.9925 | 0.9917 |
| `cwrc_plus` | `wRC+` | 0.9685 | 0.9667 |
| `cfip` | `FIP` | 0.9460 | 0.9388 |
| `cwsb` | `wSB` | 0.8955 | 0.8613 |
| `cspd` | `Spd` | 0.9124 | 0.9052 |

The rate statistics that are pure arithmetic — AVG, OBP, SLG, OPS, ISO, BABIP,
BB%, K%, ERA, WHIP, K/9, BB/9, K-BB% — reproduce the removed columns **exactly**
(maximum absolute difference 0.000000 across 26,826 batting rows; about 1e-6 for
the innings-denominated pitching rates, from rounding in the stored values).
This is why the cache stores counting statistics only: nothing was lost.

There is a sharper way to put the wOBA result. `cwoba` and the metric it
replaces are *both* linear functions of the same six counting statistics. In any
model that already has singles, doubles, triples, home runs, walks, hit-by-pitch
and plate appearances as inputs, neither adds information — each lies exactly in
the span of the others. What these metrics provide is interpretability, not
signal. The only content not recoverable from the counting statistics is the
park adjustment, which is discussed below.

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
  runs, which is not enough to fit event weights. Division III also has a gap at
  2011, when it stopped reporting walks, hit-by-pitch and sacrifice flies.
  Advanced metrics return `None` for those seasons rather than a fabricated
  value.
- **Division II has no sacrifice-hit data** in any season. This does not affect
  the metrics: the plate-appearance denominator is `AB + BB + HBP + SF`, which
  excludes sacrifice hits by construction.
- **`cspd` uses Major League calibration constants.** Its formula is published
  and unmodified, but the constants inside it were fitted to Major League play,
  so the NCAA population does not center on the conventional 5.0 — qualified
  Division I hitters average about 3.9, and 5.0 is roughly the 80th percentile.
  Compare players to each other rather than to the usual scale. It is the
  weakest metric here and is informational only; every input is retained, so
  prefer those for modelling.
- **`cwsb` correlates least well** (r = 0.90) of the run-value metrics, because
  it is a small-magnitude quantity — a standard deviation of about one run — so
  modest absolute disagreements read as large relative ones.

## Player identity

`player_id` is assigned by this package, not inherited from any source. It is
stable within a major version. Splits and merges may occur in minor releases and
are always recorded in `src/data/player_registry/player_id_aliases.csv` with a
reason; a retired id is never reassigned to a different person. Use
`resolve_player_id()` to follow an alias chain. Ids are never renumbered in a
patch release.

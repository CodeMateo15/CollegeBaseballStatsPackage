"""Derive NCAA linear weights and league constants from the team-stats cache.

This is a pure function of ``src/data/team_stats_cache/`` -- public NCAA data,
no private inputs -- so the output is reproducible from a clean checkout and
tests/test_league_constants.py asserts it regenerates byte-identically.

    python tools/build_league_constants.py

Method
------
Per (division, season), over team-seasons carrying the full batting event set:

    PA = AB + BB + HBP + SF
    y  = R / PA
    X  = [1B, 2B, 3B, HR, BB, HBP, SB, CS] / PA
    weighted least squares, weight = PA

Outs are the omitted category, so each coefficient is the marginal runs from
turning one out into that event -- the "runs above out" quantity wOBA needs.
The intercept is a nuisance term and is not used downstream.

The plate-appearance denominator excludes sacrifice hits, matching wOBA's
convention. That is deliberate: Division II never reports SH, and any
denominator including it would make Division II inconsistent with the others.

Per-season coefficients are then shrunk toward the division's pooled estimate
(empirical Bayes). The between-season spread of the raw estimates is about the
same size as their within-season standard error, so most of the year-to-year
movement is sampling noise rather than a shifting run environment; publishing
the unshrunk numbers would make every downstream rate metric jitter for no
baseball reason. Scaling terms (lg_obp, lg_r_pa) are computed from full-league
totals, are precisely estimated, and are left to vary freely by season.
"""

import argparse
import csv
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from ncaa_bbStats._paths import data_path, load_team_stats  # noqa: E402

DIVISIONS = (1, 2, 3)
SEASONS = range(2002, 2027)

# Events entering the run-value regression, in output order.
EVENTS = ("1b", "2b", "3b", "hr", "bb", "hbp", "sb", "cs")
# Events entering cwOBA's numerator. Stolen bases are modelled separately
# (cwSB) because baserunning is not a plate-appearance outcome.
WOBA_EVENTS = ("1b", "2b", "3b", "hr", "bb", "hbp")

# A team-season below this many plate appearances is a fragment (a partial
# season or a scraping artifact) and is excluded from the fit.
MIN_PA = 200
# Below this many usable teams a season's own estimate is too noisy to use;
# fall back to the division's pooled weights.
MIN_TEAMS_FOR_SEASON_FIT = 60


def ip_to_float(value):
    """Convert NCAA innings notation to true innings.

    NCAA writes partial innings as tenths: 417.1 means 417 and one out, 417.2
    means 417 and two outs. Reading it as a decimal understates outs and
    inflates every innings-denominated rate.

    Args:
        value: Innings pitched as reported (ex. ``417.2``).

    Returns:
        float | None: Innings as a real number (ex. ``417.667``), or None.
    """
    if value is None:
        return None
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    whole = int(value)
    tenths = round(value - whole, 1)
    if tenths == 0.1:
        return whole + 1.0 / 3.0
    if tenths == 0.2:
        return whole + 2.0 / 3.0
    return float(whole) if tenths == 0.0 else value


def team_batting_events(stats):
    """Extract the batting event counts needed for the regression.

    Args:
        stats (dict): One team's cached stat mapping.

    Returns:
        dict | None: Event counts plus ``pa`` and ``r``, or None if any
        required field is absent.
    """
    required = ("AB", "H", "2B", "3B", "HR", "BB (Batting)", "HBP", "SF",
                "SB", "CS", "R (Batting)")
    if any(stats.get(k) is None for k in required):
        return None

    ab = float(stats["AB"])
    hits = float(stats["H"])
    doubles = float(stats["2B"])
    triples = float(stats["3B"])
    homers = float(stats["HR"])
    walks = float(stats["BB (Batting)"])
    hbp = float(stats["HBP"])
    sac_fly = float(stats["SF"])

    singles = hits - doubles - triples - homers
    pa = ab + walks + hbp + sac_fly
    if pa < MIN_PA or singles < 0:
        return None

    return {
        "1b": singles, "2b": doubles, "3b": triples, "hr": homers,
        "bb": walks, "hbp": hbp,
        "sb": float(stats["SB"]), "cs": float(stats["CS"]),
        "pa": pa, "r": float(stats["R (Batting)"]),
    }


def collect_season(year, division):
    """Return the usable team-season event rows for one season."""
    try:
        teams = load_team_stats(year, division)
    except FileNotFoundError:
        return []
    rows = [team_batting_events(s) for s in teams.values()]
    return [r for r in rows if r is not None]


def fit_run_values(rows):
    """Weighted least squares of runs per PA on event rates.

    Args:
        rows (list[dict]): Team-season event rows from :func:`collect_season`.

    Returns:
        tuple: ``(beta, stderr, r2, rmse_runs, n)`` where ``beta`` and
        ``stderr`` are dicts keyed by event name. ``beta`` excludes the
        intercept.
    """
    n = len(rows)
    pa = np.array([r["pa"] for r in rows])
    y = np.array([r["r"] for r in rows]) / pa
    X = np.column_stack(
        [np.ones(n)] + [np.array([r[e] for r in rows]) / pa for e in EVENTS]
    )

    w = pa / pa.mean()
    sw = np.sqrt(w)
    Xw, yw = X * sw[:, None], y * sw

    coef, *_ = np.linalg.lstsq(Xw, yw, rcond=None)
    resid = yw - Xw @ coef
    dof = n - X.shape[1]
    sigma2 = float(resid @ resid) / dof
    cov = sigma2 * np.linalg.inv(Xw.T @ Xw)
    se = np.sqrt(np.diag(cov))

    # Report fit quality in runs, which is interpretable, rather than in
    # runs-per-PA, which is not.
    pred_runs = (X @ coef) * pa
    actual_runs = y * pa
    ss_res = float(((actual_runs - pred_runs) ** 2).sum())
    ss_tot = float(((actual_runs - actual_runs.mean()) ** 2).sum())
    r2 = 1.0 - ss_res / ss_tot if ss_tot else float("nan")
    rmse = float(np.sqrt(ss_res / n))

    beta = {e: float(coef[i + 1]) for i, e in enumerate(EVENTS)}
    stderr = {e: float(se[i + 1]) for i, e in enumerate(EVENTS)}
    return beta, stderr, r2, rmse, n


# Hit types in strictly increasing order of value. A home run is a triple plus a
# guaranteed run, so its run value cannot be lower; likewise down the chain.
_MONOTONE_CHAIN = ("1b", "2b", "3b", "hr")


def enforce_monotone_hits(beta, stderr):
    """Project the hit-type run values onto the order physics requires.

    An unconstrained fit puts the triple above the home run in 34 of 55
    division-seasons, including Division II's pooled estimate. That is not a
    real effect: triples occur in well under 1% of plate appearances, so their
    coefficient is the noisiest in the model, and it absorbs rally context that
    belongs elsewhere. Left alone it would overrate triples-heavy hitters in
    every downstream metric.

    Uses pool-adjacent-violators (isotonic regression) weighted by inverse
    variance, so a violation is resolved by moving the less precisely estimated
    coefficient further. Coefficients already in order are untouched.

    Args:
        beta (dict): Run values by event.
        stderr (dict): Standard errors by event, used as weights.

    Returns:
        dict: A copy of `beta` with the hit chain made non-decreasing.
    """
    blocks = []
    for event in _MONOTONE_CHAIN:
        se = stderr.get(event, 1.0)
        weight = 1.0 / (se * se) if se > 0 else 1.0
        blocks.append([beta[event], weight, [event]])

    i = 0
    while i < len(blocks) - 1:
        if blocks[i][0] <= blocks[i + 1][0]:
            i += 1
            continue
        value_a, weight_a, events_a = blocks[i]
        value_b, weight_b, events_b = blocks[i + 1]
        pooled = (value_a * weight_a + value_b * weight_b) / (weight_a + weight_b)
        blocks[i:i + 2] = [[pooled, weight_a + weight_b, events_a + events_b]]
        i = max(i - 1, 0)

    out = dict(beta)
    for value, _weight, events in blocks:
        for event in events:
            out[event] = value
    return out


def shrink(season_fits, pooled_beta):
    """Shrink each season's coefficients toward the division's pooled estimate.

    Empirical Bayes: the between-season variance of the raw estimates is split
    into a true signal component and the sampling noise implied by the
    within-season standard errors. Whatever is left after removing the noise is
    the weight given to the season's own estimate.

    Args:
        season_fits (dict): ``{year: (beta, stderr, ...)}`` for one division.
        pooled_beta (dict): The division's pooled coefficients.

    Returns:
        dict: ``{year: {event: (shrunk_beta, lambda)}}``.
    """
    out = {}
    tau2 = {}
    for event in EVENTS:
        estimates = np.array([f[0][event] for f in season_fits.values()])
        variances = np.array([f[1][event] ** 2 for f in season_fits.values()])
        # Negative means the observed spread is smaller than the noise floor,
        # i.e. no detectable real variation -- collapse fully to pooled.
        tau2[event] = max(0.0, float(estimates.var(ddof=1) - variances.mean()))

    for year, (beta, stderr, *_rest) in season_fits.items():
        row = {}
        for event in EVENTS:
            se2 = stderr[event] ** 2
            lam = tau2[event] / (tau2[event] + se2) if (tau2[event] + se2) > 0 else 0.0
            row[event] = (lam * beta[event] + (1 - lam) * pooled_beta[event], lam)
        out[year] = row
    return out


def league_batting_totals(year, division):
    """Sum the league's batting events for a season, for scaling terms."""
    rows = collect_season(year, division)
    if not rows:
        return None
    totals = {k: sum(r[k] for r in rows) for k in ("1b", "2b", "3b", "hr", "bb",
                                                   "hbp", "sb", "cs", "pa", "r")}
    totals["n_teams"] = len(rows)
    return totals


def pitching_constants(year, division):
    """Compute the season's FIP constant and league pitching rates.

    The team cache has no home-runs-allowed field in any season, and no
    ``BB (Pitching)`` before 2011 (2012 for Division III). League totals from
    the batting side stand in: within a division every hit allowed is a hit by
    someone, so the aggregates agree to within a couple of percent. The
    substitution is recorded per row so a consumer can see it.
    """
    try:
        teams = load_team_stats(year, division)
    except FileNotFoundError:
        return None

    ip = er = so = bb = hbp = hr = 0.0
    n = 0
    bb_source = hr_source = "pitching"
    for stats in teams.values():
        innings = ip_to_float(stats.get("IP"))
        if innings is None or innings <= 0 or stats.get("ER") is None:
            continue
        if stats.get("SO") is None:
            continue

        walks = stats.get("BB (Pitching)")
        if walks is None:
            walks = stats.get("BB (Batting)")
            bb_source = "batting_proxy"
        if walks is None:
            continue

        # HB is hit batters (pitching side); HBP is hit by pitch (batting side).
        hit_batters = stats.get("HB")
        if hit_batters is None:
            hit_batters = stats.get("HBP")
        if hit_batters is None:
            continue

        homers = stats.get("HR")  # home runs hit; no allowed field exists
        if homers is None:
            continue
        hr_source = "batting_proxy"

        ip += innings
        er += float(stats["ER"])
        so += float(stats["SO"])
        bb += float(walks)
        hbp += float(hit_batters)
        hr += float(homers)
        n += 1

    if n < MIN_TEAMS_FOR_SEASON_FIT or ip <= 0:
        return None

    lg_era = 9.0 * er / ip
    fip_component = (13.0 * hr + 3.0 * (bb + hbp) - 2.0 * so) / ip
    return {
        "n_teams": n,
        "lg_era": lg_era,
        "lg_ip": ip,
        "lg_hr": hr,
        "lg_bb_pit": bb,
        "lg_hbp": hbp,
        "lg_so": so,
        "cfip_constant": lg_era - fip_component,
        "bb_allowed_source": bb_source,
        "hr_allowed_source": hr_source,
    }


def build():
    """Compute every constant table. Returns (batting_rows, pitching_rows)."""
    batting_rows, pitching_rows = [], []

    for division in DIVISIONS:
        season_fits = {}
        all_rows = []
        for year in SEASONS:
            rows = collect_season(year, division)
            if len(rows) < MIN_TEAMS_FOR_SEASON_FIT:
                continue
            season_fits[year] = fit_run_values(rows)
            all_rows.extend(rows)

        if not season_fits:
            continue

        pooled_raw, pooled_se, pooled_r2, pooled_rmse, pooled_n = fit_run_values(all_rows)
        pooled_beta = enforce_monotone_hits(pooled_raw, pooled_se)
        shrunk = shrink(season_fits, pooled_beta)

        for year, (raw_beta, stderr, r2, rmse, n) in season_fits.items():
            totals = league_batting_totals(year, division)
            # Shrink first, then constrain: shrinkage pulls a noisy season toward
            # the pooled estimate, and the projection cleans up whatever ordering
            # violation survives that.
            beta = enforce_monotone_hits(
                {e: shrunk[year][e][0] for e in EVENTS}, stderr
            )

            lg_obp = sum(totals[e] for e in WOBA_EVENTS) / totals["pa"]
            raw_woba = sum(beta[e] * totals[e] for e in WOBA_EVENTS) / totals["pa"]
            scale = lg_obp / raw_woba if raw_woba else float("nan")

            # Baserunning run value per opportunity, so cwSB is centred at zero
            # for a league-average runner.
            opportunities = totals["1b"] + totals["bb"] + totals["hbp"]
            lg_wsb_per_opp = (
                (beta["sb"] * totals["sb"] + beta["cs"] * totals["cs"]) / opportunities
                if opportunities else 0.0
            )

            row = {
                "year": year, "division": division,
                "n_teams": totals["n_teams"], "n_team_seasons": n,
            }
            for event in EVENTS:
                row[f"w_{event}"] = round(scale * beta[event], 6)
            for event in EVENTS:
                row[f"lambda_{event}"] = round(shrunk[year][event][1], 4)
            row.update({
                "cwoba_scale": round(scale, 6),
                "lg_obp": round(lg_obp, 6),
                "lg_cwoba": round(lg_obp, 6),
                "lg_r_pa": round(totals["r"] / totals["pa"], 6),
                "lg_wsb_per_opp": round(scale * lg_wsb_per_opp, 6),
                # Hard-set so adding real park factors later is a data change,
                # not a schema change. No public NCAA park data exists.
                "park_factor": 1.0,
                "r2": round(r2, 4),
                "rmse_runs": round(rmse, 2),
                "method": "shrunk_season",
            })
            batting_rows.append(row)

        # Record the pooled fit so the shrinkage target is auditable.
        batting_rows.append({
            "year": 0, "division": division,
            "n_teams": 0, "n_team_seasons": pooled_n,
            **{f"w_{e}": round(pooled_beta[e], 6) for e in EVENTS},
            **{f"lambda_{e}": 0.0 for e in EVENTS},
            "cwoba_scale": 1.0, "lg_obp": 0.0, "lg_cwoba": 0.0, "lg_r_pa": 0.0,
            "lg_wsb_per_opp": 0.0, "park_factor": 1.0,
            "r2": round(pooled_r2, 4), "rmse_runs": round(pooled_rmse, 2),
            "method": "pooled_unscaled_run_values",
        })

        for year in SEASONS:
            constants = pitching_constants(year, division)
            if constants is None:
                continue
            pitching_rows.append({
                "year": year, "division": division,
                "n_teams": constants["n_teams"],
                "lg_era": round(constants["lg_era"], 4),
                "lg_ip": round(constants["lg_ip"], 1),
                "lg_hr": int(constants["lg_hr"]),
                "lg_bb_pit": int(constants["lg_bb_pit"]),
                "lg_hbp": int(constants["lg_hbp"]),
                "lg_so": int(constants["lg_so"]),
                "cfip_constant": round(constants["cfip_constant"], 4),
                "bb_allowed_source": constants["bb_allowed_source"],
                "hr_allowed_source": constants["hr_allowed_source"],
                "method": "league_totals",
            })

    batting_rows.sort(key=lambda r: (r["division"], r["year"]))
    pitching_rows.sort(key=lambda r: (r["division"], r["year"]))
    return batting_rows, pitching_rows


def write_csv(path, rows):
    """Write rows to CSV with a stable column order and LF line endings."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="\n", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows):4d} rows -> {os.path.relpath(path)}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", default=data_path("league_constants"),
                        help="Output directory (default: src/data/league_constants).")
    args = parser.parse_args(argv)

    batting_rows, pitching_rows = build()
    write_csv(os.path.join(args.out, "batting_weights.csv"), batting_rows)
    write_csv(os.path.join(args.out, "pitching_constants.csv"), pitching_rows)

    seasons = sorted({r["year"] for r in batting_rows if r["year"]})
    manifest = {
        "generator": "tools/build_league_constants.py",
        "source": "src/data/team_stats_cache (NCAA official team statistics)",
        "seasons_with_weights": {
            str(d): sorted(r["year"] for r in batting_rows
                           if r["division"] == d and r["year"])
            for d in DIVISIONS
        },
        "min_pa": MIN_PA,
        "min_teams_for_season_fit": MIN_TEAMS_FOR_SEASON_FIT,
        "events": list(EVENTS),
        "woba_events": list(WOBA_EVENTS),
        "pa_definition": "AB + BB + HBP + SF",
        "park_factor": "not modelled; fixed at 1.0 (no public NCAA park data)",
    }
    with open(os.path.join(args.out, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)
        f.write("\n")

    print(f"\nseasons with weights: {min(seasons)}-{max(seasons)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

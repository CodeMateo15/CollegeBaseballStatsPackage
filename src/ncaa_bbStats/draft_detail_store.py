"""Fetch and cache MLB Stats API draft records.

Run as a script; importing this module has no side effects.

    python -m ncaa_bbStats.draft_detail_store --years 2021 2022 2023 2024 2025 2026
    python -m ncaa_bbStats.draft_detail_store --from-dir path/to/raw/json

The API returns roughly 2 MB per draft year, most of it prose. Only the fields
the package actually reads are kept, which takes the six shipped years from
11.6 MB to under 2 MB. Dropped:

- ``blurb`` -- MLB Pipeline editorial scouting prose. It is 238 KB of the 2024
  file on its own, no function reads it, and it is the one field here with a
  real authorship claim attached. The ``scoutingReport`` video URL is kept, so
  the material is still reachable at the source.
- ``headshotLink`` -- 92 KB of URLs that can be reconstructed from the player id.
- The 30-odd redundant name spellings on each ``person`` record.

Requires the ``scrape`` extra (``pip install "ncaa_bbStats[scrape]"``) only when
fetching; reading the cache needs nothing.
"""

import argparse
import glob
import json
import os
import time

from ncaa_bbStats._paths import data_path

STATSAPI_DRAFT_URL = "https://statsapi.mlb.com/api/v1/draft/{year}"
USER_AGENT = "ncaa_bbStats/1.2 (+https://github.com/CodeMateo15/CollegeBaseballStatsPackage)"

DEFAULT_YEARS = list(range(2021, 2027))

# Requests per second is not the constraint here; being a polite client is.
REQUEST_DELAY_SECONDS = 0.5


def _int(value):
    """Parse an int from the API's stringly-typed numerics, or None."""
    if value in (None, "", "0"):
        # Post-round-10 picks carry pickValue as the literal string "0", which
        # is truthy. Storing 0.0 there would misreport those picks as having a
        # slot value of nothing rather than no published slot at all.
        return None
    try:
        return int(float(str(value).replace(",", "")))
    except (TypeError, ValueError):
        return None


def trim_pick(pick: dict, year: int) -> dict:
    """Reduce one API pick record to the fields the package uses.

    Args:
        pick (dict): A pick object from the Stats API.
        year (int): The draft year.

    Returns:
        dict: The trimmed record.
    """
    person = pick.get("person") or {}
    school = pick.get("school") or {}
    team = pick.get("team") or {}
    position = person.get("primaryPosition") or {}

    return {
        "year": year,
        "pick": pick.get("pickNumber"),
        "round": pick.get("pickRound"),
        "round_pick": pick.get("roundPickNumber"),
        "prospect_rank": pick.get("rank"),
        "slot_value": _int(pick.get("pickValue")),
        "signing_bonus": _int(pick.get("signingBonus")),
        "is_drafted": pick.get("isDrafted"),
        "is_pass": pick.get("isPass"),
        # Club identity is stored as the MLBAM id, not the name. Franchise
        # renames (Indians/Guardians, the Athletics' three cities) then need no
        # mapping table at all.
        "team_id": team.get("id"),
        "team_name": team.get("name"),
        "name": person.get("fullName"),
        "mlbam_id": person.get("id"),
        "birth_date": person.get("birthDate"),
        "age": person.get("currentAge"),
        "height": person.get("height"),
        "weight": person.get("weight"),
        "position": position.get("abbreviation"),
        "bats": (person.get("batSide") or {}).get("code"),
        "throws": (person.get("pitchHand") or {}).get("code"),
        "birth_city": person.get("birthCity"),
        "birth_state": person.get("birthStateProvince"),
        "birth_country": person.get("birthCountry"),
        "school": school.get("name"),
        # "4YR JR", "4YR SR", "JC J2" and so on. This states a player's class
        # directly, which is otherwise inferred.
        "school_class": school.get("schoolClass"),
        "school_state": school.get("state"),
        "school_country": school.get("country"),
        "scouting_report_url": pick.get("scoutingReport"),
    }


def trim_draft(payload: dict) -> list:
    """Flatten and trim a whole draft-year payload into a list of picks."""
    drafts = payload.get("drafts") or {}
    year = int(drafts.get("draftYear") or 0)
    picks = []
    for round_ in drafts.get("rounds") or []:
        for pick in round_.get("picks") or []:
            picks.append(trim_pick(pick, year))
    picks.sort(key=lambda p: (p["pick"] is None, p["pick"]))
    return picks


def fetch_year(year: int) -> dict:
    """Fetch one draft year from the Stats API.

    Args:
        year (int): Draft year.

    Returns:
        dict: The raw API payload.

    Raises:
        ImportError: If the ``scrape`` extra is not installed.
    """
    try:
        import requests
    except ImportError as exc:  # pragma: no cover - depends on the environment
        raise ImportError(
            "Fetching draft data needs the scrape extra: "
            'pip install "ncaa_bbStats[scrape]"'
        ) from exc

    response = requests.get(
        STATSAPI_DRAFT_URL.format(year=year),
        headers={"User-Agent": USER_AGENT},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def write_year(year: int, picks: list, out_dir: str) -> str:
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{year}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(picks, f, separators=(",", ":"), sort_keys=True)
    return path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--years", type=int, nargs="+", default=DEFAULT_YEARS)
    parser.add_argument("--out", default=data_path("draft_detail"))
    parser.add_argument(
        "--from-dir",
        help="Trim already-downloaded statsapi_draft_*.json instead of fetching.",
    )
    args = parser.parse_args(argv)

    total_picks = 0
    for year in args.years:
        if args.from_dir:
            matches = glob.glob(os.path.join(args.from_dir, f"*{year}*.json"))
            if not matches:
                print(f"  {year}: no raw file found, skipping")
                continue
            with open(matches[0], encoding="utf-8") as f:
                payload = json.load(f)
        else:
            print(f"fetching {year}...")
            payload = fetch_year(year)
            time.sleep(REQUEST_DELAY_SECONDS)

        picks = trim_draft(payload)
        if not picks:
            print(f"  {year}: no picks returned, not writing")
            continue

        path = write_year(year, picks, args.out)
        college = sum(
            1 for p in picks if (p["school_class"] or "").startswith(("4YR", "JC"))
        )
        size_kb = os.path.getsize(path) / 1024
        print(f"  {year}: {len(picks):4d} picks ({college:3d} college) "
              f"-> {os.path.relpath(path)}  {size_kb:.0f} KB")
        total_picks += len(picks)

    print(f"\n{total_picks} picks cached")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

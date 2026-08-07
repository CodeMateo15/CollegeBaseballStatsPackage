"""Canonical team identity: one id per program, across every data source.

Each dataset spells schools its own way. NCAA team stats say ``"Eastern Ill."``,
the player leaderboards say ``"EIU"``, draft records say ``"Eastern Illinois
University"``, and RPI says ``"Eastern Illinois"``. This module maps all of them
onto one ``team_id``, so datasets can be joined.

    >>> resolve_team("Eastern Ill.")
    'IPEDS:148496'
    >>> resolve_team("EIU") == resolve_team("Eastern Illinois")
    True

Identity notes
--------------
The id is the federal IPEDS unitid where one is known (``"IPEDS:230171"``),
because it survives rebrands -- Dixie State and Utah Tech share an id, as do
Houston Baptist and Houston Christian. Programs with no unitid get a minted
``"NCAA:<slug>"`` id.

**Division is not part of identity.** A program that changes division keeps one
id and one history; division is recorded per season by :func:`team_seasons`.

Deliberately uses the standard library rather than pandas, so importing it stays
cheap for callers that only need a name lookup.
"""

import csv
import os
from functools import lru_cache
from typing import Optional

from ncaa_bbStats._normalize import normalize_school
from ncaa_bbStats._paths import data_path

__all__ = [
    "as_team_id",
    "resolve_team",
    "resolve_team_verbose",
    "team_info",
    "team_aliases",
    "list_teams",
    "list_conferences",
    "team_seasons",
    "team_division",
    "team_conference",
    "crosswalk",
    "NAMESPACES",
]

#: Alias namespaces, one per source. Keeping them separate means a wrong alias
#: in one source cannot affect lookups against another.
NAMESPACES = (
    "ncaa_short",
    "ncaa_label",
    "fg_acronym",
    "fg_full",
    "rpi",
    "eada_institution",
    "almanac_school",
)

_OPEN_ENDED = 9999


class Resolution:
    """The outcome of a name lookup, with enough detail to audit it.

    Attributes:
        team_id (str): The canonical id.
        matched_alias (str): The stored spelling that matched.
        namespace (str): Which source that spelling came from.
        method (str): ``"exact"`` if the spelling matched verbatim, or
            ``"normalized"`` if it matched only after folding.
    """

    __slots__ = ("team_id", "matched_alias", "namespace", "method")

    def __init__(self, team_id, matched_alias, namespace, method):
        self.team_id = team_id
        self.matched_alias = matched_alias
        self.namespace = namespace
        self.method = method

    def __repr__(self):
        return (
            f"Resolution(team_id={self.team_id!r}, "
            f"matched_alias={self.matched_alias!r}, "
            f"namespace={self.namespace!r}, method={self.method!r})"
        )

    def __eq__(self, other):
        if isinstance(other, Resolution):
            return (self.team_id, self.matched_alias, self.namespace,
                    self.method) == (other.team_id, other.matched_alias,
                                     other.namespace, other.method)
        return NotImplemented


def _read(name):
    path = data_path("registry", name)
    if not os.path.isfile(path):
        raise FileNotFoundError(
            f"Team registry not found: {path}. "
            "Run `python tools/build_team_registry.py`."
        )
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


@lru_cache(maxsize=1)
def _teams():
    return {row["team_id"]: row for row in _read("teams.csv")}


@lru_cache(maxsize=1)
def _aliases():
    return _read("team_aliases.csv")


@lru_cache(maxsize=1)
def _seasons():
    rows = _read("team_seasons.csv")
    for row in rows:
        row["season"] = int(row["season"])
        row["division"] = int(row["division"])
    return rows


@lru_cache(maxsize=1)
def _alias_index():
    """Build the lookup tables once.

    Returns:
        tuple: ``(exact, normalized)``, each mapping a key to a list of
        ``(team_id, alias, namespace, valid_from, valid_to)``.
    """
    exact, normalized = {}, {}
    for row in _aliases():
        entry = (
            row["team_id"], row["alias"], row["namespace"],
            int(row["valid_from"]), int(row["valid_to"]),
        )
        exact.setdefault(row["alias"], []).append(entry)
        normalized.setdefault(row["alias_norm"], []).append(entry)
    return exact, normalized


def _matches(candidates, season, namespace, division):
    """Filter candidate aliases by season, namespace and division."""
    out = []
    for entry in candidates:
        team_id, _alias, entry_namespace, valid_from, valid_to = entry
        if namespace and entry_namespace != namespace:
            continue
        if season is not None and not (valid_from <= season <= valid_to):
            continue
        if division is not None:
            divisions = {
                s["division"] for s in _seasons()
                if s["team_id"] == team_id
                and (season is None or s["season"] == season)
            }
            if division not in divisions:
                continue
        out.append(entry)
    return out


def as_team_id(team: str, *, season: Optional[int] = None) -> Optional[str]:
    """Accept either a ``team_id`` or a name, and return a ``team_id``.

    Every public function that takes a team accepts both, so callers can pass
    the id they already have without a round trip through a name.

    Args:
        team (str): A ``team_id`` or any known spelling.
        season (int, optional): Restrict name resolution to that season.

    Returns:
        str | None: The ``team_id``, or None if unknown.
    """
    if not team:
        return None
    if team in _teams():
        return team
    return resolve_team(team, season=season)


def resolve_team_verbose(
    name: str,
    *,
    season: Optional[int] = None,
    namespace: Optional[str] = None,
    division: Optional[int] = None,
) -> Optional[Resolution]:
    """Resolve a team name, reporting how the match was made.

    Args:
        name (str): A team or school name in any supported spelling.
        season (int, optional): Restrict to aliases valid that season. Needed to
            tell a rebrand apart -- ``"Dixie State"`` is only valid through 2022.
        namespace (str, optional): Restrict to one source's spellings. See
            :data:`NAMESPACES`.
        division (int, optional): Require the program to have played this
            division (that season, if ``season`` is given).

    Returns:
        Resolution | None: The match, or None if the name is unknown or
        ambiguous.
    """
    if not name:
        return None

    exact, normalized = _alias_index()

    for method, key, table in (
        ("exact", name.strip(), exact),
        ("normalized", normalize_school(name), normalized),
    ):
        candidates = _matches(table.get(key, []), season, namespace, division)
        if not candidates:
            continue
        team_ids = {entry[0] for entry in candidates}
        if len(team_ids) > 1:
            # Genuinely ambiguous -- refuse rather than pick one. Passing a
            # season or division usually settles it.
            return None
        team_id, alias, entry_namespace, _from, _to = candidates[0]
        return Resolution(team_id, alias, entry_namespace, method)

    return None


def resolve_team(
    name: str,
    *,
    season: Optional[int] = None,
    namespace: Optional[str] = None,
    division: Optional[int] = None,
) -> Optional[str]:
    """Map any spelling of a team name to its canonical ``team_id``.

    Matching is exact first, then against a folded form that absorbs the
    mechanical differences between sources (``"Alabama St."`` and ``"Alabama
    State"``, ``"Ark.-Pine Bluff"`` and ``"Arkansas-Pine Bluff"``). Genuine
    naming disagreements are handled by stored aliases, not by guessing: there
    is no fuzzy fallback, because a silent near-match is how two programs get
    swapped without anyone noticing.

    Args:
        name (str): A team or school name in any supported spelling.
        season (int, optional): Restrict to aliases valid that season.
        namespace (str, optional): Restrict to one source's spellings.
        division (int, optional): Require the program to have played this division.

    Returns:
        str | None: The ``team_id``, or None if unknown or ambiguous.

    Examples:
        >>> resolve_team("Northeastern")
        'IPEDS:167358'
        >>> resolve_team("Dixie State", season=2022) == resolve_team("Utah Tech")
        True
    """
    resolution = resolve_team_verbose(
        name, season=season, namespace=namespace, division=division
    )
    return resolution.team_id if resolution else None


def team_info(team: str, season: Optional[int] = None) -> Optional[dict]:
    """Return a program's identity record.

    Args:
        team (str): A ``team_id`` or any known spelling.
        season (int, optional): Include that season's division and conference.

    Returns:
        dict | None: Identity fields, plus ``division`` and ``conference`` when
        ``season`` is given. None if the team is unknown.
    """
    team_id = team if team in _teams() else resolve_team(team, season=season)
    if not team_id:
        return None

    row = dict(_teams()[team_id])
    row["first_season"] = int(row["first_season"])
    row["last_season"] = int(row["last_season"])
    row["divisions"] = [int(d) for d in row["divisions"].split("|") if d]

    if season is not None:
        match = next(
            (s for s in _seasons()
             if s["team_id"] == team_id and s["season"] == season),
            None,
        )
        row["season"] = season
        row["division"] = match["division"] if match else None
        row["conference"] = match["league"] if match else None
    return row


def team_aliases(team: str, namespace: Optional[str] = None) -> list[str]:
    """Every known spelling of a program.

    Args:
        team (str): A ``team_id`` or any known spelling.
        namespace (str, optional): Restrict to one source. See :data:`NAMESPACES`.

    Returns:
        list[str]: Sorted unique spellings.
    """
    team_id = team if team in _teams() else resolve_team(team)
    if not team_id:
        return []
    return sorted({
        row["alias"] for row in _aliases()
        if row["team_id"] == team_id
        and (namespace is None or row["namespace"] == namespace)
    })


def team_seasons(team: str) -> list[dict]:
    """A program's season-by-season division and conference.

    Args:
        team (str): A ``team_id`` or any known spelling.

    Returns:
        list[dict]: One dict per season with ``season``, ``division``,
        ``conference``, and the NCAA spelling used, sorted by season.
    """
    team_id = team if team in _teams() else resolve_team(team)
    if not team_id:
        return []
    return [
        {
            "season": row["season"],
            "division": row["division"],
            "conference": row["league"],
            "ncaa_short": row["ncaa_short"],
        }
        for row in sorted(
            (s for s in _seasons() if s["team_id"] == team_id),
            key=lambda s: (s["season"], s["division"]),
        )
    ]


def team_division(team: str, season: int) -> Optional[int]:
    """Which division a program played in a given season.

    Args:
        team (str): A ``team_id`` or any known spelling.
        season (int): Season year.

    Returns:
        int | None: 1, 2, or 3, or None if the program has no record that season.
    """
    return next(
        (s["division"] for s in team_seasons(team) if s["season"] == season), None
    )


def team_conference(team: str, season: int) -> Optional[str]:
    """Which conference a program played in a given season.

    Args:
        team (str): A ``team_id`` or any known spelling.
        season (int): Season year.

    Returns:
        str | None: The conference code, or None if unknown that season.
    """
    return next(
        (s["conference"] for s in team_seasons(team) if s["season"] == season), None
    )


def list_teams(
    season: Optional[int] = None,
    division: Optional[int] = None,
    conference: Optional[str] = None,
) -> list[dict]:
    """List programs, optionally filtered by season, division, and conference.

    Args:
        season (int, optional): Only programs with a record that season.
        division (int, optional): Only programs in this division.
        conference (str, optional): Only programs in this conference
            (case-insensitive).

    Returns:
        list[dict]: Identity records sorted by canonical name.
    """
    matching = set()
    for row in _seasons():
        if season is not None and row["season"] != season:
            continue
        if division is not None and row["division"] != division:
            continue
        if conference is not None and row["league"].lower() != conference.lower():
            continue
        matching.add(row["team_id"])

    teams = [team_info(team_id) for team_id in matching]
    return sorted(teams, key=lambda t: t["canonical_name"])


def list_conferences(season: int, division: Optional[int] = None) -> list[str]:
    """List the conferences active in a season.

    Args:
        season (int): Season year.
        division (int, optional): Restrict to one division.

    Returns:
        list[str]: Sorted conference codes.
    """
    return sorted({
        row["league"] for row in _seasons()
        if row["season"] == season
        and row["league"]
        and (division is None or row["division"] == division)
    })


def crosswalk(
    from_namespace: str, to_namespace: str, season: Optional[int] = None
) -> dict:
    """Map one source's spellings directly onto another's.

    Useful for bulk joins where going through ``team_id`` row by row would be
    awkward.

    Args:
        from_namespace (str): Source namespace. See :data:`NAMESPACES`.
        to_namespace (str): Target namespace.
        season (int, optional): Restrict to aliases valid that season.

    Returns:
        dict: ``{from_spelling: to_spelling}``. Entries with no counterpart in
        the target namespace are omitted.
    """
    def spellings(namespace):
        out = {}
        for row in _aliases():
            if row["namespace"] != namespace:
                continue
            if season is not None and not (
                int(row["valid_from"]) <= season <= int(row["valid_to"])
            ):
                continue
            out.setdefault(row["team_id"], row["alias"])
        return out

    source = spellings(from_namespace)
    target = spellings(to_namespace)
    return {
        alias: target[team_id]
        for team_id, alias in source.items()
        if team_id in target
    }

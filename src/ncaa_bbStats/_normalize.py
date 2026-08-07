"""Shared string normalizers for team, school, and player names.

These are pure functions with no data dependencies, so any module can import
them without pulling in pandas or the optional scraping extras.

This module is private. Nothing here is re-exported from ``ncaa_bbStats``.
"""

import re
import unicodedata

__all__ = [
    "split_team_league",
    "strip_league",
    "strip_all_parens",
    "normalize_school",
    "school_key",
]


def split_team_league(team_league_str: str) -> tuple[str, str]:
    """Split an NCAA ``"Team Name (League)"`` label into its two parts.

    Only the final parenthesised group is treated as the league. Many schools
    carry a state disambiguator that is part of their identity -- there are two
    distinct programs named Anderson, Augustana, Bethel, Carroll, and Centenary,
    told apart only by ``(IN)`` vs ``(SC)``, ``(IL)`` vs ``(SD)``, and so on.
    Stripping every parenthesised group merges them.

    Args:
        team_league_str (str): A label such as ``"Miami (OH) (MAC)"``.

    Returns:
        tuple[str, str]: ``(team, league)``. The league is ``""`` when the label
        has no parenthesised suffix.

    Examples:
        >>> split_team_league("Northeastern (CAA)")
        ('Northeastern', 'CAA')
        >>> split_team_league("Miami (OH) (MAC)")
        ('Miami (OH)', 'MAC')
    """
    if "(" in team_league_str:
        team, league = team_league_str.rsplit("(", 1)
        return team.strip(), league.rstrip(")").strip()
    return team_league_str.strip(), ""


def strip_league(team_league_str: str) -> str:
    """Return just the team name from a ``"Team Name (League)"`` label.

    Args:
        team_league_str (str): A label such as ``"Augustana (SD) (NSIC)"``.

    Returns:
        str: The team name, keeping any state disambiguator.
    """
    return split_team_league(team_league_str)[0]


# Retained for callers that genuinely want every parenthesised group removed.
_ALL_PARENS = re.compile(r"\s*\(.*?\)")


def strip_all_parens(name: str) -> str:
    """Remove every parenthesised group from a name.

    Prefer :func:`strip_league` for NCAA team labels; this collapses schools
    that are distinguished only by a state suffix.

    Args:
        name (str): Any name.

    Returns:
        str: The name with all parenthesised groups removed.
    """
    return _ALL_PARENS.sub("", name).strip()


# Each source spells schools its own way. NCAA abbreviates ("Alabama St.",
# "Ark.-Pine Bluff"), Warren Nolan spells out ("Alabama State",
# "Arkansas-Pine Bluff"), Baseball Almanac uses legal names ("Arizona State
# University"), and IPEDS uses charter names ("Alabama A & M University").
# These substitutions fold the mechanical differences so only genuine naming
# disagreements need an explicit alias row.
_ABBREVIATIONS = [
    (r"\bst\b", "state"),          # NCAA "St." for State; see _SAINT_PREFIX below
    (r"\bstate\b", "state"),
    (r"\buniv\b", "university"),
    (r"\bu\b", "university"),
    (r"\bcoll\b", "college"),
    (r"\bintl\b", "international"),
    (r"\bmil\b", "military"),
    (r"\bacad\b", "academy"),
    (r"\btech\b", "technological"),
    (r"\bpoly\b", "polytechnic"),
    # Directional words the NCAA clips.
    (r"\bso\b", "southern"),
    (r"\bno\b", "northern"),
    (r"\bcent\b", "central"),
    (r"\bval\b", "valley"),
    (r"\batl\b", "atlantic"),
]

# State names as the NCAA abbreviates them. This is where most of the
# cross-source disagreement lives: NCAA writes "Eastern Ill.", Warren Nolan
# writes "Eastern Illinois", and neither is wrong.
_STATE_ABBREVIATIONS = {
    "ala": "alabama", "ariz": "arizona", "ark": "arkansas",
    "calif": "california", "cal": "california", "colo": "colorado",
    "conn": "connecticut", "del": "delaware", "fla": "florida",
    "ga": "georgia", "ill": "illinois", "ind": "indiana",
    "kan": "kansas", "ky": "kentucky", "la": "louisiana",
    "md": "maryland", "mass": "massachusetts", "mich": "michigan",
    "minn": "minnesota", "miss": "mississippi", "mo": "missouri",
    "mont": "montana", "neb": "nebraska", "nev": "nevada",
    "okla": "oklahoma", "ore": "oregon", "penn": "pennsylvania",
    "pa": "pennsylvania", "tenn": "tennessee", "tex": "texas",
    "va": "virginia", "vt": "vermont", "wash": "washington",
    "wis": "wisconsin", "wyo": "wyoming",
    "caro": "carolina", "nc": "north carolina", "sc": "south carolina",
}

# Words that carry no distinguishing information once everything else is folded.
_NOISE_WORDS = {"the", "of", "at", "university", "college", "univ"}

# "St." before a name is Saint (St. John's); after or alone it is State
# (Alabama St.). Handled before the abbreviation pass, which assumes State.
_SAINT_PREFIX = re.compile(r"\bst\.?\s+(?=[a-z])")


def _fold_accents(text: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c)
    )


def normalize_school(name: str) -> str:
    """Fold a school name to a comparable form, keeping its distinguishing words.

    Lowercases, strips accents and punctuation, expands the abbreviations each
    source prefers, and drops filler words. The result is not meant to be shown
    to anyone -- it exists so ``"Alabama St."`` and ``"Alabama State"`` compare
    equal without a hand-written alias.

    Args:
        name (str): A school or team name from any source.

    Returns:
        str: The folded form.

    Examples:
        >>> normalize_school("Alabama St.")
        'alabama state'
        >>> normalize_school("Arizona State University")
        'arizona state'
        >>> normalize_school("St. John's")
        'saint johns'
    """
    if not name:
        return ""

    raw = str(name).strip()

    # A bare all-caps token is an acronym, not a name: leave it alone. Expanding
    # it collides with real schools -- Virginia Tech's "VT" would otherwise
    # become "vermont", and "LA", "PA" and "MD" are similarly overloaded.
    if len(raw) <= 5 and raw.isupper() and raw.isalnum():
        return raw.lower()

    text = _fold_accents(raw).lower().strip()
    text = text.replace("&", " and ")
    text = _SAINT_PREFIX.sub("saint ", text)
    text = re.sub(r"[.’']", "", text)
    text = re.sub(r"[^a-z0-9]+", " ", text).strip()

    for pattern, replacement in _ABBREVIATIONS:
        text = re.sub(pattern, replacement, text)

    words = [
        _STATE_ABBREVIATIONS.get(w, w)
        for w in text.split()
        if w not in _NOISE_WORDS
    ]
    # A state abbreviation can expand to two words ("nc" -> "north carolina").
    words = " ".join(words).split()
    # Collapse a doubled "state state" produced by expanding "St." next to an
    # already-spelled-out "State".
    deduped = [w for i, w in enumerate(words) if i == 0 or w != words[i - 1]]
    return " ".join(deduped)


def school_key(name: str) -> str:
    """Aggressively folded school key, for matching across unrelated sources.

    Like :func:`normalize_school` but also drops directional and descriptive
    words that some sources include and others omit. Looser, so it matches more
    and is likelier to collide -- use it only where a false match is caught by a
    second signal.

    Args:
        name (str): A school or team name.

    Returns:
        str: The folded key.
    """
    text = normalize_school(name)
    return " ".join(w for w in text.split() if w not in {"main", "campus", "system"})

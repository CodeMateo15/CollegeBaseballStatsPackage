"""Documentation invariants.

Sphinx runs without autodoc here, so every function signature in the docs is
hand-written. Nothing but these tests stops the docs drifting from the code, or
the downloadable CSVs drifting from the data they were derived from.
"""

import hashlib
import pathlib
import re
import sys

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = REPO_ROOT / "docs"
STATIC_DATA = DOCS / "_static" / "data"
sys.path.insert(0, str(REPO_ROOT / "src"))

import ncaa_bbStats  # noqa: E402

# Names that are documented conceptually rather than as a py:function entry.
DOCS_EXEMPT: set[str] = set()


def _documented_names() -> set[str]:
    """Every name given a `.. py:function::` directive anywhere in docs/."""
    pattern = re.compile(r"^\.\.\s+py:function::\s*([A-Za-z_][A-Za-z0-9_]*)", re.M)
    names = set()
    for path in DOCS.glob("*.rst"):
        names.update(pattern.findall(path.read_text(encoding="utf-8")))
    return names


def test_every_public_name_is_documented():
    """Each name in __all__ has a signature block in some docs page."""
    documented = _documented_names()
    missing = sorted(set(ncaa_bbStats.__all__) - documented - DOCS_EXEMPT)
    assert not missing, (
        "public names with no `.. py:function::` entry in docs/: "
        f"{missing}. Add them, or add them to DOCS_EXEMPT with a reason."
    )


def test_docs_do_not_document_removed_names():
    """Catches signature blocks left behind after a function is renamed."""
    documented = _documented_names()
    package_names = set(dir(ncaa_bbStats)) | set(ncaa_bbStats.__all__)
    # Names documented in the advanced-stats page that live on the module.
    import ncaa_bbStats.advanced_stats as adv
    import ncaa_bbStats.player_utils as pu

    package_names |= set(dir(adv)) | set(dir(pu))

    stale = sorted(documented - package_names)
    assert not stale, f"docs describe functions that no longer exist: {stale}"


def test_toctree_entries_all_resolve():
    """Every document listed in index.rst exists."""
    index = (DOCS / "index.rst").read_text(encoding="utf-8")
    referenced = set()
    for block in re.finditer(r"\.\.\s+toctree::(.*?)(?=\n\S|\Z)", index, re.S):
        for line in block.group(1).splitlines():
            line = line.strip()
            if line and not line.startswith(":"):
                referenced.add(line)

    missing = sorted(n for n in referenced if not (DOCS / f"{n}.rst").is_file())
    assert not missing, f"index.rst references missing documents: {missing}"


def test_no_references_to_removed_data_files():
    """The docs must not link download files that no longer exist."""
    dangling = []
    for path in DOCS.glob("*.rst"):
        text = path.read_text(encoding="utf-8")
        for target in re.findall(r":download:`[^<]*<([^>]+)>`", text):
            resolved = (DOCS / target.lstrip("/")).resolve()
            if not resolved.is_file():
                dangling.append(f"{path.name} -> {target}")
    assert not dangling, f"dangling :download: targets: {dangling}"


@pytest.mark.skipif(
    not (STATIC_DATA / "MANIFEST.txt").is_file(), reason="static data manifest absent"
)
def test_static_data_is_current():
    """The published CSVs match the source data they were generated from.

    Regenerate with `python docs/make_static_data.py` when this fails.
    """
    manifest = (STATIC_DATA / "MANIFEST.txt").read_text(encoding="utf-8")
    stale = []
    for line in manifest.splitlines():
        if line.startswith("#") or not line.strip():
            continue
        source, published, expected_digest, _rows = line.split("\t")

        source_path = REPO_ROOT / source
        if not source_path.is_file():
            stale.append(f"{source} (source missing)")
            continue
        if not (STATIC_DATA / published).is_file():
            stale.append(f"{published} (published copy missing)")
            continue

        digest = hashlib.sha256()
        with source_path.open("rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                digest.update(chunk)
        if digest.hexdigest() != expected_digest:
            stale.append(f"{source} changed since {published} was generated")

    assert not stale, (
        "docs/_static/data is stale; rerun `python docs/make_static_data.py`:\n  "
        + "\n  ".join(stale)
    )


def test_provenance_documents_every_shipped_dataset():
    """Each directory under src/data appears in DATA_PROVENANCE.md."""
    provenance = (REPO_ROOT / "DATA_PROVENANCE.md").read_text(encoding="utf-8")
    data_dir = REPO_ROOT / "src" / "data"

    undocumented = [
        d.name
        for d in sorted(data_dir.iterdir())
        if d.is_dir() and not d.name.startswith(".") and d.name not in provenance
    ]
    assert not undocumented, (
        f"data directories missing from DATA_PROVENANCE.md: {undocumented}"
    )


def test_readme_names_only_real_functions():
    """A README that promises a function which does not exist is worse than none."""
    import re

    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    # Non-function backticked terms that legitimately appear in prose.
    allowed_prose = {
        "model", "explain", "scrape", "all", "dev", "tools", "team_id",
        "player_id", "cwrc", "pip", "qualified", "noMin", "carried_forward",
        "eada_year", "significant", "coverage", "confidence", "report",
    }
    named = set(re.findall(r"`([a-z_][a-z0-9_]*)`", readme))
    missing = sorted(
        name for name in named
        if name not in allowed_prose and not hasattr(ncaa_bbStats, name)
    )
    assert not missing, f"README names functions that do not exist: {missing}"


def test_version_is_consistent_across_metadata():
    """pyproject and CITATION.cff must agree."""
    import re
    import tomllib

    with open(REPO_ROOT / "pyproject.toml", "rb") as f:
        pyproject_version = tomllib.load(f)["project"]["version"]

    citation = (REPO_ROOT / "CITATION.cff").read_text(encoding="utf-8")
    citation_version = re.search(r"^version:\s*(\S+)", citation, re.M).group(1)

    assert pyproject_version == citation_version, (
        f"pyproject says {pyproject_version}, CITATION.cff says {citation_version}"
    )


def test_season_stat_year_ranges_match_the_data():
    """The ranges in season_stats.rst must be what the cache actually contains.

    They were maintained by hand and had drifted: all 47 were stale on the end
    year after 2026 landed, and 14 had start years that never matched the data
    at all.
    """
    from ncaa_bbStats._paths import load_team_stats

    first, last = {}, {}
    for division in (1, 2, 3):
        for season in range(2002, 2027):
            try:
                teams = load_team_stats(season, division)
            except FileNotFoundError:
                continue
            keys = set()
            for stats in teams.values():
                keys |= {
                    k for k, v in stats.items() if isinstance(v, (int, float))
                }
            for key in keys:
                last[key] = max(last.get(key, 0), season)
                first[key] = min(first.get(key, 9999), season)

    documented = re.findall(
        r"\*\*(.+?)\*\*:.*?\((\d{4}) - (\d{4})\)",
        (DOCS / "season_stats.rst").read_text(encoding="utf-8"),
    )
    assert documented, "no stat entries found in season_stats.rst"

    wrong = []
    for name, doc_first, doc_last in documented:
        if name not in first:
            wrong.append(f"{name}: documented but absent from the cache")
        elif (int(doc_first), int(doc_last)) != (first[name], last[name]):
            wrong.append(
                f"{name}: docs say {doc_first}-{doc_last}, "
                f"data has {first[name]}-{last[name]}"
            )
    assert not wrong, "stale year ranges in season_stats.rst:\n  " + "\n  ".join(wrong)


def test_documented_stats_cover_what_the_cache_ships():
    """Every stat in the cache is documented somewhere."""
    from ncaa_bbStats._paths import load_team_stats

    keys = set()
    for division in (1, 2, 3):
        stats = load_team_stats(2026, division)
        for values in stats.values():
            keys |= {k for k, v in values.items() if isinstance(v, (int, float))}

    reference = (DOCS / "season_stats.rst").read_text(encoding="utf-8")
    undocumented = sorted(k for k in keys if f"**{k}**" not in reference)
    assert not undocumented, (
        f"stats shipped but not in season_stats.rst: {undocumented}"
    )

"""Packaging invariants.

These guard the two failure modes that shipped in past releases:

1. `MANIFEST.in` read `recursive-include src/data/team_stats_cache/div2*.json`
   (no space before the glob), so no Division II data reached any wheel. Nothing
   caught it because the package imports fine without those files -- reads just
   raise FileNotFoundError at runtime.
2. `__init__.py` imported `draft_stats`, which imports `requests` and `bs4` at
   module scope, but neither was a declared dependency -- so `import ncaa_bbStats`
   failed on a clean install.
"""

import ast
import pathlib
import subprocess
import sys
import zipfile

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = REPO_ROOT / "src"
PKG = SRC / "ncaa_bbStats"
DATA = SRC / "data"

# Every data directory the package reads at runtime. Each must survive into a
# built wheel or the corresponding public functions raise FileNotFoundError.
REQUIRED_WHEEL_DATA_DIRS = [
    "data/team_stats_cache/div1",
    "data/team_stats_cache/div2",
    "data/team_stats_cache/div3",
    "data/player_stats_cache/batting",
    "data/player_stats_cache/pitching",
    "data/player_stats_cache_ncaa/batting",
    "data/player_stats_cache_ncaa/pitching",
    "data/mlb_draft_cache",
    "data/mlb_team_names",
    "data/team_names_stats",
]

# Third-party modules the package may import at module scope without an extra.
# Anything outside this set must be imported lazily, inside the function that
# needs it, so `import ncaa_bbStats` works with only the base dependencies.
BASE_DEPENDENCIES = {"numpy", "pandas"}

# Modules that legitimately require an optional extra. They are never imported
# eagerly from __init__.py.
OPTIONAL_DEP_MODULES = {
    "team_stats.py": {"curl_cffi", "bs4"},
    "draft_stats.py": {"requests", "bs4"},
    "draft_store.py": {"requests", "bs4"},
}

STDLIB = set(sys.stdlib_module_names)


def _toplevel_imports(path: pathlib.Path) -> set[str]:
    """Return the top-level module names imported at module scope in `path`."""
    tree = ast.parse(path.read_text(), filename=str(path))
    names = set()
    for node in tree.body:  # module scope only, not inside functions
        if isinstance(node, ast.Import):
            names.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names.add(node.module.split(".")[0])
    return names


@pytest.fixture(scope="session")
def wheel_namelist(tmp_path_factory):
    """Build a wheel once and return the list of paths inside it."""
    outdir = tmp_path_factory.mktemp("wheel")
    result = subprocess.run(
        [sys.executable, "-m", "build", "--wheel", "--outdir", str(outdir), str(REPO_ROOT)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        pytest.skip(f"wheel build unavailable: {result.stderr[-400:]}")

    wheels = list(outdir.glob("*.whl"))
    assert len(wheels) == 1, f"expected one wheel, got {wheels}"
    with zipfile.ZipFile(wheels[0]) as z:
        return z.namelist()


@pytest.mark.parametrize("directory", REQUIRED_WHEEL_DATA_DIRS)
def test_wheel_contains_data_directory(wheel_namelist, directory):
    """Every runtime data directory ships. This is the div2 regression test."""
    matches = [f for f in wheel_namelist if f.startswith(directory + "/")]
    assert matches, f"{directory} is missing from the wheel"


def test_wheel_has_all_team_stat_seasons(wheel_namelist):
    """All three divisions ship the same 2002-2026 span."""
    for division in (1, 2, 3):
        prefix = f"data/team_stats_cache/div{division}/"
        seasons = {
            int(f[len(prefix):-len(".json")])
            for f in wheel_namelist
            if f.startswith(prefix) and f.endswith(".json")
        }
        assert seasons == set(range(2002, 2027)), (
            f"division {division} ships {len(seasons)} seasons, expected 25"
        )


def test_wheel_ships_no_stray_modules(wheel_namelist):
    """No .py file under data/ -- those are dev scripts, not package code."""
    stray = [f for f in wheel_namelist if f.startswith("data/") and f.endswith(".py")]
    assert not stray, f"dev scripts packaged as modules: {stray}"


def test_wheel_excludes_docs(wheel_namelist):
    """Docs assets belong in the sdist only, not inside site-packages."""
    assert not [f for f in wheel_namelist if f.startswith("docs/")]


def test_wheel_excludes_junk(wheel_namelist):
    """No .DS_Store or bytecode."""
    junk = [f for f in wheel_namelist if "DS_Store" in f or f.endswith(".pyc")]
    assert not junk, f"junk files in wheel: {junk}"


def test_manifest_patterns_all_match_something():
    """Every recursive-include in MANIFEST.in matches at least one real file.

    A pattern that matches nothing is exactly how the div2 typo hid: the build
    succeeded and said nothing.
    """
    manifest = (REPO_ROOT / "MANIFEST.in").read_text().splitlines()
    unmatched = []
    for line in manifest:
        line = line.strip()
        if not line.startswith("recursive-include src/data"):
            continue
        _, directory, *patterns = line.split()
        base = REPO_ROOT / directory
        if not base.is_dir():
            unmatched.append(f"{directory} (not a directory)")
            continue
        if not any(any(base.rglob(p)) for p in patterns):
            unmatched.append(line)
    assert not unmatched, f"MANIFEST.in patterns matching nothing: {unmatched}"


def test_import_does_not_require_optional_extras():
    """`import ncaa_bbStats` must work with only the base dependencies.

    Runs in a subprocess with the optional extras blocked, so an eager import of
    requests/bs4/curl_cffi/xgboost fails here rather than for a user.
    """
    blocked = ["requests", "bs4", "curl_cffi", "xgboost", "shap", "matplotlib"]
    program = f"""
import sys
class Blocker:
    def find_module(self, name, path=None):
        if name.split('.')[0] in {blocked!r}:
            raise ImportError(f'{{name}} is blocked by this test')
        return None
sys.meta_path.insert(0, Blocker())
sys.path.insert(0, {str(SRC)!r})
import ncaa_bbStats
assert ncaa_bbStats.list_all_teams(2025, 1)
print('ok')
"""
    result = subprocess.run(
        [sys.executable, "-c", program], capture_output=True, text=True
    )
    assert result.returncode == 0, (
        "import ncaa_bbStats requires an optional dependency:\n" + result.stderr[-1500:]
    )


@pytest.mark.parametrize(
    "module", sorted(p.name for p in PKG.glob("*.py")), ids=lambda m: m
)
def test_module_imports_declare_their_dependencies(module):
    """Only base dependencies may be imported at module scope, unless declared."""
    allowed = BASE_DEPENDENCIES | OPTIONAL_DEP_MODULES.get(module, set())
    imported = _toplevel_imports(PKG / module)
    third_party = {
        name
        for name in imported
        if name not in STDLIB and name != "ncaa_bbStats"
    }
    undeclared = third_party - allowed
    assert not undeclared, (
        f"{module} imports {sorted(undeclared)} at module scope. Either add it to "
        "BASE_DEPENDENCIES/OPTIONAL_DEP_MODULES here and to pyproject.toml, or "
        "move the import inside the function that needs it."
    )


def test_all_exports_resolve():
    """Every name in __all__ is actually reachable, including the lazy ones."""
    sys.path.insert(0, str(SRC))
    import ncaa_bbStats

    missing = [n for n in ncaa_bbStats.__all__ if not hasattr(ncaa_bbStats, n)]
    assert not missing, f"__all__ lists unreachable names: {missing}"


def test_no_console_script_pointing_at_missing_module():
    """`[project.scripts]` must not reference a module that does not exist.

    The old `ncaa_bb = "ncaa_bbStats.main:main"` entry point pointed at a module
    that was never created, so the installed command always failed.
    """
    import tomllib

    with open(REPO_ROOT / "pyproject.toml", "rb") as f:
        config = tomllib.load(f)

    for name, target in config.get("project", {}).get("scripts", {}).items():
        module_path, _, _ = target.partition(":")
        rel = pathlib.Path(*module_path.split(".")).with_suffix(".py")
        assert (SRC / rel).exists(), (
            f"console script {name!r} points at {module_path}, which does not exist"
        )

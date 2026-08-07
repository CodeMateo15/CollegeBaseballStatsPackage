"""The demonstration notebooks stay in step with the public API.

These are cheap structural checks, not an execution run -- executing six
notebooks takes minutes and belongs in ``notebooks/build_notebooks.py``, which
refuses to write if any cell raises.

What this catches is the thing that actually goes wrong: a function added to
``__all__`` with no example, or a notebook committed carrying a stale error
output from a run that was never fixed.
"""

import json
import pathlib
import sys

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
NOTEBOOKS = REPO_ROOT / "notebooks"
sys.path.insert(0, str(REPO_ROOT / "src"))

import ncaa_bbStats  # noqa: E402

# Generated notebooks, excluding the pre-1.2.0 ones kept for reference.
CURRENT = sorted(p for p in NOTEBOOKS.glob("*.ipynb")
                 if not p.name.startswith("_legacy"))


def _source(path: pathlib.Path) -> str:
    notebook = json.loads(path.read_text(encoding="utf-8"))
    return " ".join("".join(cell["source"]) for cell in notebook["cells"])


def test_notebooks_exist():
    assert len(CURRENT) >= 6, f"expected the six demo notebooks, found {CURRENT}"


def test_every_public_function_is_demonstrated():
    """Adding a function to the public API means adding an example."""
    text = " ".join(_source(p) for p in CURRENT)
    missing = sorted(name for name in ncaa_bbStats.__all__ if name not in text)
    assert not missing, (
        f"{len(missing)} public functions have no notebook example: {missing}. "
        "Add them in notebooks/build_notebooks.py and re-run it."
    )


@pytest.mark.parametrize("path", CURRENT, ids=lambda p: p.name)
def test_notebook_has_no_error_output(path):
    """A committed notebook must not carry a traceback."""
    notebook = json.loads(path.read_text(encoding="utf-8"))
    errors = []
    for index, cell in enumerate(notebook["cells"]):
        for output in cell.get("outputs", []):
            if output.get("output_type") == "error":
                errors.append(
                    f"cell {index}: {output.get('ename')}: {output.get('evalue')}"
                )
    assert not errors, f"{path.name} has error output:\n  " + "\n  ".join(errors)


@pytest.mark.parametrize("path", CURRENT, ids=lambda p: p.name)
def test_notebook_outputs_are_saved(path):
    """Outputs ship with the notebooks so they read without being run."""
    notebook = json.loads(path.read_text(encoding="utf-8"))
    code_cells = [c for c in notebook["cells"] if c["cell_type"] == "code"]
    with_output = [c for c in code_cells if c.get("outputs")]
    assert code_cells, f"{path.name} has no code cells"
    # The import cell legitimately produces nothing.
    assert len(with_output) >= len(code_cells) - 1, (
        f"{path.name}: only {len(with_output)} of {len(code_cells)} code cells "
        "have saved output -- re-run notebooks/build_notebooks.py"
    )


@pytest.mark.parametrize("path", CURRENT, ids=lambda p: p.name)
def test_notebook_is_valid_json_and_nbformat_4(path):
    notebook = json.loads(path.read_text(encoding="utf-8"))
    assert notebook["nbformat"] == 4
    assert notebook["cells"]


def test_generator_covers_what_it_writes():
    """The generator's own coverage check agrees with this one.

    Guards against the notebooks being hand-edited out of step with the script
    that is supposed to produce them.
    """
    generator = (NOTEBOOKS / "build_notebooks.py").read_text(encoding="utf-8")
    missing = sorted(
        name for name in ncaa_bbStats.__all__ if name not in generator
    )
    assert not missing, (
        f"build_notebooks.py does not mention: {missing}"
    )

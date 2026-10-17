# HydroForge

A Python library for preparing geospatial data for hydrological and hydraulic modelling workflows.

## Development

HydroForge requires Python 3.14 or newer and uses [uv](https://docs.astral.sh/uv/) to manage the environment and dependencies. Add or remove dependencies with `uv add` and `uv remove` rather than editing `pyproject.toml` by hand.

Set up the development environment and install the Git pre-commit hook:

```bash
uv sync
uv run pre-commit install
```

Run all checks on the files on disk, staged or not, with a single command:

```bash
uv run poe check
```

It first fixes what it can automatically (lint, import order, Python and Markdown formatting), then checks the lockfile, types and tests. Review any changes it makes with `git diff`. Every step runs even if an earlier one fails, and the command reports failure at the end.

The pre-commit hook runs the same checks on staged files at every commit. If a hook fixes formatting, the commit stops; review the changes, stage them and commit again.

Docstrings follow the [NumPy convention](https://numpydoc.readthedocs.io/en/latest/format.html).

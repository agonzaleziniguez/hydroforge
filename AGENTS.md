# Working on HydroForge

Rules for everyone who changes this repository, people and AI agents.

## Code

- Keep code simple, easy to read and easy to maintain. Do not over-engineer.
- Write short, clear docstrings. All functions, including private helpers,
  document Parameters, Returns and Raises (NumPy style). Keep each description
  to one line when possible. Tests are exempt.
- Name functions with a verb, for example `check_no_overlaps` or `make_landcover`.
  Exceptions are fine when they make sense, for example `test_*` functions
  for pytest.
- Avoid duplicated logic. Extract shared code when it is the same idea,
  not just similar-looking code.
- Be consistent: follow the names, structure and patterns already in the code.
- Use one name for one idea. Don't use one word for two meanings.

## Tools

- Use uv for everything. Add and remove dependencies only with uv commands.
- Run `uv run poe check` before you commit.

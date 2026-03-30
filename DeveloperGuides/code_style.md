# Code Style Guide

This guide defines the conventions for Python code in **Spikes & Pipes**
so the codebase stays consistent.

## Section separators

Use ASCII comment separators to break major areas inside modules:

```python
# ---------------------------------------------------------------------------
# Section Title
# ---------------------------------------------------------------------------
```

Typical sections:
- Constants / Configuration
- Public API / Private helpers
- Classes (with internal separators for attributes vs methods)

## Naming and visibility

- Follow PEP 8: `snake_case` for functions, variables, and modules;
  `PascalCase` for classes; `UPPER_SNAKE_CASE` for constants.
- Private helpers use a single-underscore prefix: `_load_engine`, `_compute_units`.
- Name-mangled internals use a double-underscore prefix only when
  subclass collision avoidance is genuinely needed.
- Keep public API surface small — prefix anything not meant
  for external use with `_`.

## Function / method layout

- Keep one function signature per line when short.
- Use multiline signatures when parameters are long:

```python
def call(
    self,
    module_name: str,
    input_data: dict[str, Any],
) -> dict[str, np.ndarray]:
    ...
```

- Always add trailing commas in multiline argument lists.

## Type hints

- Add type hints to all public function signatures.
- Use built-in generics (`list`, `dict`, `tuple`) — no `typing.List` etc.
- Use `from __future__ import annotations` where needed.
- Private helpers may omit hints when the types are obvious from context.

## Blank lines for control flow

Add a blank line between logical blocks (`for`, `if`, `try`, etc.)
when it helps readability:

```python
for key, value in input_data.items():
    ...

if missing_keys:
    ...

try:
    provider = build_feature_provider(feature_dict)
except ValueError:
    ...
```

## Early returns

- Prefer early `return` / `raise` to reduce nesting.
- Keep the happy path at the lowest indentation level.

```python
def process(data: dict) -> Result:
    if not data:
        return Result.empty()

    validated = _validate(data)
    if validated is None:
        raise ValueError("Invalid input")

    return _transform(validated)
```

## Error handling

- Log recoverable errors using the module-level logger.
- Raise specific exceptions (`ValueError`, `RuntimeError`, etc.)
  instead of bare `Exception`.
- Use `sys.exit(1)` only in CLI entry points for hard failures.

## Logging

Define a module-level logger at the top of each file:

```python
import logging

logger = logging.getLogger(__name__)
```

## Docstrings

- Use Google-style docstrings for public functions and classes.
- Keep the first line as a concise summary.

```python
def load_model(path: str) -> Model:
    """Load a compiled model from disk.

    Args:
        path: Filesystem path to the model directory.

    Returns:
        Initialised Model instance ready for inference.

    Raises:
        FileNotFoundError: If *path* does not exist.
    """
```

## Misc

- Prefer `dict[str, ...]` over `Dict[str, ...]`.
- Prefer explicit types in signatures and return values.
- Keep line length at or below 90 characters (enforced by ruff).
- Ensure separator lines are 90 characters total (including `#`).
- Use `ruff` for linting and formatting.

## Tests design

- Keep test data in `tests/<name>/fixtures/` and reuse shared helpers.
- `tests/<name>/fixtures/` is gitignored; generate fixtures at runtime
  when possible.
- Prefer JSON fixtures for inputs/expected outputs.
- Keep tests focused on one behavior per test case.
- Make tests deterministic by fixing seeds and test data paths.
- For model tests, generate expected JSON from the source of truth
  (PyTorch / reference implementation) rather than hand-authored fixtures.

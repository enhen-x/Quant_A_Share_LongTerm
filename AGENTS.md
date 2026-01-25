# LANGUAGE OVERRIDE (MANDATORY)

All reasoning, planning, and responses MUST be in Chinese.
Ignore any prior English defaults.

# Repository Guidelines

## Project Structure & Module Organization

- `src/`: core Python modules organized by domain (e.g., `deviation/`, `distribution/`, `grid/`, `position/`, `risk/`).
- `scripts/`: runnable entry points for data updates, analysis, position calculation, and reporting.
- `tests/`: unit tests (mixed `pytest` and `unittest`).
- `config/`: configuration, including `config/main.yaml` for Tushare and strategy settings.
- `data/`, `results/`, `reports/`, `figures/`, `logs/`: generated artifacts and outputs; keep large data out of Git.

## Build, Test, and Development Commands

- `pip install -r requirements.txt`: install runtime dependencies.
- `python scripts/data/update_data.py`: pull and refresh market data.
- `python scripts/analysis/calc_deviation.py`: compute deviation ratios.
- `python scripts/analysis/analyze_distribution.py`: analyze deviation distributions.
- `python scripts/analysis/generate_grid.py`: generate position grids.
- `python scripts/position/calculate_position.py`: compute target positions.
- `python scripts/position/run_rebalance.py`: produce rebalancing actions.
- `python scripts/report/generate_report.py`: generate analysis reports.

## Coding Style & Naming Conventions

- Python-only codebase; use 4-space indentation and keep functions small and focused.
- Follow existing naming patterns: `snake_case` for functions/variables, `PascalCase` for classes.
- Add type hints where practical and match existing module layouts under `src/`.
- No formatter/linter is configured; keep diffs minimal and consistent with nearby code.

## Testing Guidelines

- Tests live in `tests/` and follow `test_*.py` naming.
- Use `pytest` for most tests: `python -m pytest tests/test_deviation.py -v`.
- Some tests use `unittest`: `python -m unittest tests.test_distribution`.
- Target unit coverage for core calculation logic in `src/deviation`, `src/distribution`, and `src/grid`.

## Commit & Pull Request Guidelines

- Git history is minimal; use short, descriptive commit messages (imperative is preferred).
- Exclude data artifacts and secrets; do not commit tokens from `config/main.yaml`.
- PRs should include a summary, test evidence (commands/output), and any report artifacts if relevant.

## Configuration & Data Notes

- `config/main.yaml` controls API tokens, window sizes, grid parameters, and risk limits.
- Data directories are used by scripts; keep paths stable and document any schema changes.

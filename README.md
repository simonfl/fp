# Financial Planning

Personal finance Monte Carlo simulator for long-range scenario planning.

## What It Does

This project models monthly cash flow across:

- income streams
- expenses
- transfers (for contributions/withdrawals)
- investment and retirement accounts
- simple progressive taxes
- Monte Carlo market variation

You define a scenario as a `Model` subclass (see `examples/baseline_family.py` or `main.py`) and run:

- one deterministic seeded simulation output table
- many Monte Carlo runs with percentile summaries

## Requirements

- Python `>=3.13`
- [`uv`](https://github.com/astral-sh/uv)

## Setup (uv)

Windows (PowerShell):

```powershell
uv python install 3.13
uv venv --python=3.13 .venv
uv pip install --python .venv\Scripts\python.exe -e ./
uv pip install --python .venv\Scripts\python.exe pytest
```

macOS/Linux (bash/zsh):

```bash
uv python install 3.13
uv venv --python=3.13 .venv
uv pip install --python .venv/bin/python -e ./
uv pip install --python .venv/bin/python pytest
```

## Run A Scenario

Windows (PowerShell):

```powershell
.venv\Scripts\activate
python examples/baseline_family.py
```

macOS/Linux (bash/zsh):

```bash
source .venv/bin/activate
python examples/baseline_family.py
```

Quick-start example:

Windows (PowerShell):

```powershell
uv run --python .venv\Scripts\python.exe examples/baseline_family.py
```

macOS/Linux (bash/zsh):

```bash
uv run --python .venv/bin/python examples/baseline_family.py
```

Other scenario entrypoints:

- `main.py`
- `examples/baseline_family.py`
- `examples/dual_income_nyc_family.py`
- `examples/single_parent_public_service.py`
- `examples/small_business_owner.py`
- `examples/early_retiree_coastfire.py`

These scripts are example consumers of the core engine, not part of the packaged library API.

Each script:

- runs a single simulation and prints yearly balances
- writes per-account ledgers into `ledgers/`
- runs Monte Carlo and prints percentiles

## Run Tests

Windows (PowerShell):

```powershell
uv run --python .venv\Scripts\python.exe pytest -q
```

macOS/Linux (bash/zsh):

```bash
uv run --python .venv/bin/python pytest -q
```

## Project Layout

- `src/fp_sim/sim.py`: simulation loop + Monte Carlo orchestration
- `src/fp_sim/accounts.py`: account, flow, expense, transfer, mortgage, RSU logic
- `src/fp_sim/taxes.py`: progressive tax calculations
- `src/fp_sim/util.py`: distribution sampling and ledger record formatting
- `tests/test_engine.py`: focused engine regression tests

## Notes

- Scenarios are currently script-driven rather than CLI-driven.
- Tax and market models are intentionally simplified for planning simulations, not tax filing or financial advice.

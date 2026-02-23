# Example Scenarios

These are synthetic persona-based scenarios you can run directly.

## Included Personas

- `examples/baseline_family.py`
  - Baseline dual-income family scenario with mortgage, RSUs, retirement contributions, and college funding flows.
- `examples/dual_income_nyc_family.py`
  - High-earning NYC family with RSUs, private school costs, mortgage, 401(k), Roth, and 529 plans.
- `examples/single_parent_public_service.py`
  - NYC public-service single parent with pension transition, 457(b), Roth IRA, 529, and mortgage.
- `examples/small_business_owner.py`
  - Business owner with salary + distributions, business overhead, SEP IRA, solo Roth 401(k), and cash reserve policy.
- `examples/early_retiree_coastfire.py`
  - CoastFIRE household with part-time income, taxable drawdowns, Roth/traditional IRA mix, and healthcare bridge years.

## Run

From repo root:

```powershell
python .\examples\baseline_family.py
python .\examples\dual_income_nyc_family.py
python .\examples\single_parent_public_service.py
python .\examples\small_business_owner.py
python .\examples\early_retiree_coastfire.py
```

These scripts call `mc.run_once()` and `mc.run(100)` by default.

Run all examples at once (no temp directory required):

```powershell
python .\examples\run_all_examples.py
```

import math

from hypothesis import given, settings, strategies as st

from fp_sim.accounts import Account
from fp_sim.accounts import Expense
from fp_sim.sim import Model, Sim
from fp_sim.taxes import IncomeTax


@given(
    total=st.floats(min_value=0, max_value=2_000_000, allow_nan=False, allow_infinity=False),
    marginal=st.floats(min_value=0, max_value=250_000, allow_nan=False, allow_infinity=False),
)
@settings(deadline=None)
def test_income_tax_never_negative(total, marginal):
    monthly_tax = IncomeTax.federal.tax(total, marginal)
    assert monthly_tax >= 0


@given(
    total=st.floats(min_value=0, max_value=2_000_000, allow_nan=False, allow_infinity=False),
    low=st.floats(min_value=0, max_value=125_000, allow_nan=False, allow_infinity=False),
    delta=st.floats(min_value=0, max_value=125_000, allow_nan=False, allow_infinity=False),
)
@settings(deadline=None)
def test_income_tax_is_monotonic_in_marginal_income(total, low, delta):
    high = low + delta
    tax_low = IncomeTax.federal.tax(total, low)
    tax_high = IncomeTax.federal.tax(total, high)
    assert tax_high >= tax_low


@given(
    total=st.floats(min_value=0.01, max_value=5_000_000, allow_nan=False, allow_infinity=False),
    basis_ratio=st.floats(min_value=0, max_value=1.5, allow_nan=False, allow_infinity=False),
    tax_rate=st.floats(min_value=0, max_value=0.5, allow_nan=False, allow_infinity=False),
    requested=st.floats(min_value=0, max_value=5_000_000, allow_nan=False, allow_infinity=False),
)
@settings(deadline=None)
def test_withdraw_invariants(total, basis_ratio, tax_rate, requested):
    basis = total * basis_ratio
    acct = Account(total=total, basis=basis, tax_rate=tax_rate)

    net = acct.withdraw(requested, "property")

    assert net >= 0
    assert net <= requested + 1e-6
    assert acct.balance() >= -1e-6
    assert math.isclose(acct.balance(), acct.basis + acct.gain, rel_tol=1e-9, abs_tol=1e-6)


@given(
    checking_balance=st.floats(min_value=0, max_value=500_000, allow_nan=False, allow_infinity=False),
    savings_balance=st.floats(min_value=0, max_value=500_000, allow_nan=False, allow_infinity=False),
    keep_min=st.floats(min_value=1, max_value=150_000, allow_nan=False, allow_infinity=False),
    keep_span=st.floats(min_value=0, max_value=150_000, allow_nan=False, allow_infinity=False),
)
@settings(deadline=None)
def test_keep_respects_thresholds_with_available_liquidity(
    checking_balance, savings_balance, keep_min, keep_span
):
    keep_max = keep_min + keep_span
    checking = Account(total=checking_balance)
    savings = Account(total=savings_balance)

    checking.keep(savings, [savings], keep_max=keep_max, keep_min=keep_min)

    assert checking.balance() <= keep_max + 1e-6

    if checking_balance + savings_balance >= keep_min:
        assert checking.balance() >= keep_min - 1e-6
    else:
        assert checking.balance() <= checking_balance + savings_balance + 1e-6


@given(
    start_cash=st.floats(min_value=0, max_value=1_000_000, allow_nan=False, allow_infinity=False),
    monthly_income=st.floats(min_value=100, max_value=100_000, allow_nan=False, allow_infinity=False),
    monthly_expense=st.floats(min_value=0.01, max_value=100_000, allow_nan=False, allow_infinity=False),
    years=st.integers(min_value=1, max_value=5),
)
@settings(deadline=None)
def test_sim_no_insolvency_when_monthly_income_covers_expenses(
    start_cash, monthly_income, monthly_expense, years
):
    if monthly_income < monthly_expense:
        monthly_income, monthly_expense = monthly_expense, monthly_income

    class SolventModel(Model):
        def setup(self):
            self.account("Checking", Account(total=start_cash))
            self.expense("Living", Expense(monthly=monthly_expense))

        def run(self):
            self.account("Checking").deposit(monthly_income, "Income")
            self.expense("Living").outof([self.account("Checking")])

    sim = Sim(SolventModel(), 2026, 2026 + years, summary_every_n_years=1)
    sim.run(quiet=True)
    assert sim.model.account("Checking").balance() >= -1e-6

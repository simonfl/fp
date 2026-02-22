import pytest

from fp_sim.accounts import Account, Expense
from fp_sim.sim import MC
from fp_sim.taxes import IncomeTax


class DummyAccount:
	def __init__(self, balance):
		self._balance = balance
		self.withdrawn = 0

	def balance(self):
		return self._balance

	def withdraw(self, amt, _note):
		self.withdrawn += amt
		self._balance -= amt
		return amt


def test_end_year_includes_december_when_month_not_specified():
	exp = Expense(monthly=100).end(2025)
	exp.update(2025, 12)
	assert exp.get() > 0

	exp.update(2026, 1)
	assert exp.get() == 0


def test_income_tax_negative_marginal_is_zero():
	assert IncomeTax.federal.tax(0, -1000) == 0


def test_income_tax_clear_empties_pending_taxes():
	acct = DummyAccount(1000)
	IncomeTax.city.calculate([acct])
	assert len(IncomeTax.city.taxes) > 0

	IncomeTax.city.clear()
	assert IncomeTax.city.taxes == []


def test_mc_requires_positive_iterations():
	with pytest.raises(ValueError):
		MC(model=None, start=2023, end=2024).run(0)


def test_taxable_withdrawal_caps_at_max_net_and_never_overdraws():
	acct = Account(total=100, basis=0, tax_rate=0.2)
	net = acct.withdraw(100, "liquidate")

	assert net == pytest.approx(80)
	assert acct.balance() == pytest.approx(0)
	assert acct.basis == pytest.approx(0)
	assert acct.gain == pytest.approx(0)


def test_taxable_withdrawal_preserves_proportional_basis_and_gain():
	acct = Account(total=200, basis=100, tax_rate=0.2)
	net = acct.withdraw(90, "spend")

	assert net == pytest.approx(90)
	assert acct.basis == pytest.approx(50)
	assert acct.gain == pytest.approx(50)
	assert acct.balance() == pytest.approx(100)


def test_withdrawal_from_loss_position_has_no_tax_credit():
	acct = Account(total=80, basis=100, tax_rate=0.2)
	net = acct.withdraw(80, "sell")

	assert net == pytest.approx(80)
	assert acct.balance() == pytest.approx(0)
	assert acct.ledger[-1].tax == pytest.approx(0)


def test_withdrawal_handles_taxable_fraction_above_one():
	acct = Account(total=100, basis=-20, tax_rate=0.2)
	net = acct.withdraw(10, "sell")

	assert net == pytest.approx(10)
	assert acct.balance() < 100


def test_federal_brackets_updated_to_2026_mfj():
	assert IncomeTax.federal.brackets[:3] == [24800, 100800, 211400]
	assert IncomeTax.federal.brackets[-2] == 768700


def test_ny_and_nyc_brackets_use_mfj_schedule():
	assert IncomeTax.state.brackets[:3] == [17150, 23600, 27900]
	assert IncomeTax.state.brackets[-3:] == [5000000, 25000000, 999999999]
	assert IncomeTax.city.brackets == [21600, 45000, 90000, 999999999]

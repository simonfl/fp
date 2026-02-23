import pytest

from fp_sim.accounts import Account, Expense, Transfer
from fp_sim.sim import MC, Model, Sim
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


def test_starter_model_simulation_completes_and_has_summary():
	class SmokeModel(Model):
		def setup(self):
			self.account("Checking", Account(total=25000))
			self.expense("Living", Expense(monthly=1000))

		def run(self):
			self.expense("Living").outof([self.account("Checking")])

	sim = Sim(SmokeModel(), 2026, 2027, summary_every_n_years=1)
	sim.run(quiet=True)
	assert 2026 in sim.summary
	assert "Total" in sim.summary[2026]


def test_sim_label_truncates_long_headers():
	class EmptyModel(Model):
		def setup(self):
			pass

	sim = Sim(EmptyModel(), 2026, 2027)
	assert sim.label("Databricks 401k Traditional", 13) == "Databricks..."


def test_federal_tax_math_at_known_points():
	# $12,000 annual taxable income at 10% => $1,200 annual tax => $100/month.
	assert IncomeTax.federal.tax(0, 1000) == pytest.approx(100)

	# Starting at $24,000 annual, tax $2,400 additional:
	#  $800 at 10% + $1,600 at 12% = $272 annual => $22.666.../month.
	assert IncomeTax.federal.tax(2000, 200) == pytest.approx(272 / 12)


def test_account_keep_sweeps_down_to_keep_max():
	checking = Account(total=120000)
	savings = Account(total=50000)

	checking.keep(savings, [savings], keep_max=100000, keep_min=50000)

	assert checking.balance() == pytest.approx(100000)
	assert savings.balance() == pytest.approx(70000)


def test_account_keep_refills_up_to_keep_min():
	checking = Account(total=1000)
	savings = Account(total=10000)

	checking.keep(savings, [savings], keep_max=100000, keep_min=5000)

	assert checking.balance() == pytest.approx(5000)
	assert savings.balance() == pytest.approx(6000)


def test_expense_allows_explicit_zero_monthly():
	exp = Expense(monthly=0)
	exp.update(2026, 1)
	assert exp.get() == 0


def test_transfer_allows_explicit_zero_monthly():
	tr = Transfer(monthly=0)
	tr.update(2026, 1)
	assert tr.amt == 0


def test_withdraw_preserves_tiny_remaining_balance():
	checking = Account(total=1.0)
	savings = Account(total=0)

	checking.keep(savings, [savings], keep_max=0.00006103515625, keep_min=0.00006103515625)
	assert checking.balance() == pytest.approx(0.00006103515625)

from fp_sim.accounts import Account, Expense, Income
from fp_sim.sim import MC, Model
from fp_sim.util import Dist


class StarterModel(Model):
	def setup(self):
		self.income("Salary", Income(annually=150000, increase=Dist(0.03, 0.01), bonus=0.1))
		self.account("Income", Account())
		self.account("Checking", Account(total=25000))
		self.account(
			"Brokerage",
			Account(total=100000, basis=80000, beta=0.8, alpha=Dist(0.02, 0.03), tax_rate=0.2),
		)
		self.expense("Living costs", Expense(monthly=6000, variation=500, increase=Dist(0.03, 0.005)))

	def run(self):
		income = self.account("Income")
		checking = self.account("Checking")
		brokerage = self.account("Brokerage")

		self.income("Salary").into(income)
		income.into(checking)
		self.expense("Living costs").outof([checking, brokerage])
		checking.keep(brokerage, [brokerage], keep_max=30000, keep_min=15000)


def main():
	model = StarterModel()
	mc = MC(model, 2026, 2050)
	mc.run_once()
	model.report("ledgers")
	mc.run(100, summary_every_n_years=5)


if __name__ == "__main__":
	main()

#!/usr/bin/env python3

from fp_sim.sim import Model, MC
from fp_sim.util import Dist, Ledger
from fp_sim.taxes import IncomeTax
from fp_sim.accounts import Income, RSU, Account, Mortgage, Expense, Transfer

class Model1(Model):
	def __init__(self):
		super().__init__()

	def setup(self):

		self.JASON_RETIREMENT = 2035
		self.SELENE_RETIREMENT = 2038

		self.income('Jason paycheck',  Income(annually=150000, increase=Dist(0.03, 0.02), bonus=0.10).end(self.JASON_RETIREMENT))
		self.income('Selene paycheck', Income(annually=130000, increase=Dist(0.03, 0.005), bonus=0.05).end(self.SELENE_RETIREMENT))

		stock_price = Account(total=42.0, beta=0.1, alpha=Dist(0.02, 0.1))
		self.income('Stock', stock_price)

		self.income('RSU 1', RSU(quarterly_qty=200, price=stock_price).end(2022, 4))
		self.income('RSU 2', RSU(quarterly_qty=120, price=stock_price).end(2023, 4))

		self.account('Income', Account())
		self.account('RSUs', Account())

		self.account('Checking', Account(total=26000, category='Investments'))
		self.account('Merrill', Account(total=210000, basis=150000, beta=0.2, alpha=Dist(0.01, 0.005), tax_rate=0.2, category='Investments'))
		self.account('ETrade', Account(total=82000, basis=51000, beta=1.5, alpha=Dist(0.0, 0.03), tax_rate=0.2, category='Investments'))

		self.account('Jason 401k', Account(total=148000, beta=0.8, alpha=Dist(0.01, 0.005), category='Retirement').start(2040))
		self.account('Jason IRA', Account(total=230000, beta=0.8, alpha=Dist(0.00, 0.005), category='Retirement').start(2040))
		self.account('Jason Roth', Account(total=57000, beta=0.8, alpha=Dist(0.00, 0.005), category='Retirement').start(2040))

		self.account('Selene 401k', Account(total=230000, beta=0.8, alpha=Dist(0.00, 0.005), category='Retirement').start(2043))
		self.account('Selene IRA', Account(total=98000, beta=0.8, alpha=Dist(0.00, 0.005), category='Retirement').start(2043))
		self.account('Selene Roth', Account(total=157000, beta=0.8, alpha=Dist(0.00, 0.005), category='Retirement').start(2043))

		self.account('College 529', Account(total=98000, beta=0.6, alpha=Dist(0.00, 0.005)))

		self.account('Mortgage 1A', Mortgage(balance=612800, payment=2421.30, rate=0.025, category='Real estate').end(2051))
		self.account('Apt 1A', Account(total=945000, alpha=Dist(0.02, 0.005), category='Real estate'))

		self.expense('Credit card', Expense(monthly=3500, variation=800, increase=Dist(0.03, 0.005)))
		self.expense('Nanny', Expense(monthly=2500, variation=200, increase=Dist(0.05, 0)).end(2026))

		self.expense('Anna college', Expense(annually=50000).start(2030).end(2034))
		self.expense('Mara college', Expense(annually=60000).start(2034).end(2038))
		self.expense('Wally college', Expense(annually=65000).start(2036).end(2040))
		self.expense('Travel', Expense(annually=2000, variation=500, increase=Dist(0.03, 0)))

		self.transfer('Jason 401k', Transfer(annually=19500, increase=Dist(0.03, 0)).end(self.JASON_RETIREMENT))
		self.transfer('Selene 401k', Transfer(annually=19500, increase=Dist(0.03, 0)).end(self.SELENE_RETIREMENT))
		self.transfer('Pre-tax retirement income', Transfer(annually=120000, increase=Dist(0.03, 0)))
		self.transfer('Post-tax retirement income', Transfer(annually=60000, increase=Dist(0.03, 0)))
		self.transfer('College savings', Transfer(annually=10000, increase=Dist(0, 0)).end(2025))

	def run(self):
		gross_income = self.account('Income')
		gross_rsus = self.account('RSUs')

		checking = self.account('Checking')
		ml = self.account('Merrill')
		etrade = self.account('ETrade')
		j401k = self.account('Jason 401k')
		s401k = self.account('Selene 401k')
		roth = self.account('Jason Roth')
		college = self.account('College 529')

		retirement_accounts = [
			j401k, s401k, 
			self.account('Jason IRA'), 
			self.account('Selene IRA'), 
		]

		roth_accounts = [
			self.account('Jason Roth'),
			self.account('Selene Roth'),
		]

		savings_accounts = [ml, etrade]
		expense_accounts = [checking] + savings_accounts + roth_accounts

		mortgage = self.account('Mortgage 1A')

		# Income
		self.income('Jason paycheck').into(gross_income)
		self.income('Selene paycheck').into(gross_income)

		self.income('RSU 1').into(gross_rsus)
		self.income('RSU 2').into(gross_rsus)

		self.transfer('Jason 401k').go([gross_income], j401k)
		self.transfer('Selene 401k').go([gross_income], s401k)

		# Retirement income
		self.transfer('Pre-tax retirement income').go(retirement_accounts, gross_income)

		# Pre-tax expenses
		mortgage.interest_outof([gross_income] + expense_accounts)

		# Taxes
		IncomeTax.federal.calculate([gross_income, gross_rsus])
		IncomeTax.city.calculate([gross_income, gross_rsus])

		# Fund college accounts (pre-tax for state)
		self.transfer('College savings').go([gross_income] + expense_accounts, college)

		IncomeTax.state.calculate([gross_income, gross_rsus])

		IncomeTax.federal.commit()
		IncomeTax.state.commit()
		IncomeTax.city.commit()

		# Retirement income (Roth)
		self.transfer('Post-tax retirement income').go(roth_accounts, gross_income)

		# Post-tax income goes into checking and investment accounts
		gross_income.into(checking)
		gross_rsus.into(etrade)

		# Expenses
		for exp in self.expenses.values():
			if 'college' in exp.name:
				exp.outof([college] + expense_accounts)
			else:
				exp.outof(expense_accounts)

		mortgage.principal_outof(expense_accounts)

		# Pay off mortgage
		if self.year == 2050 and self.month == 12:
			mortgage.into(checking)

		# Balance checking and savings
		checking.keep(ml, savings_accounts, 20000)

		etrade.sweep(ml, 250000)


def main():
	model = Model1()
	mc = MC(model, 2021, 2070)

	# Run a single simulation and display yearly account totals
	mc.run_once()

	# Write out ledgers files containing all individual transactions for the latest simulation run
	model.report('ledgers')

	# Run 100 simulations and summarize the range of outcomes
	mc.run(100)


if __name__ == '__main__':
	main()


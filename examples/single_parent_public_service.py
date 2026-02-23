#!/usr/bin/env python3

from fp_sim.sim import Model, MC
from fp_sim.util import Dist
from fp_sim.taxes import IncomeTax
from fp_sim.accounts import Income, Account, Mortgage, Expense, Transfer


class SingleParentPublicService(Model):
    def __init__(self):
        super().__init__()

    def setup(self):
        self.RETIREMENT = 2051

        self.income(
            "Teacher salary",
            Income(annually=128000, increase=Dist(0.025, 0.005), bonus=0.0).end(self.RETIREMENT),
        )
        self.income(
            "Summer stipend",
            Income(annually=18000, increase=Dist(0.02, 0.005), bonus=0.0, every_n_month=12),
        )
        self.income(
            "Pension income",
            Income(annually=62000, increase=Dist(0.02, 0.0), bonus=0.0).start(self.RETIREMENT + 1),
        )

        self.account("Income", Account())

        self.account("Checking", Account(total=45000, category="Cash"))
        self.account(
            "Brokerage",
            Account(total=180000, basis=140000, beta=0.6, alpha=Dist(0.01, 0.015), tax_rate=0.15, category="Investments"),
        )
        self.account(
            "457b",
            Account(total=230000, beta=0.75, alpha=Dist(0.01, 0.01), category="Retirement").start(self.RETIREMENT + 1),
        )
        self.account(
            "Roth IRA",
            Account(total=90000, beta=0.8, alpha=Dist(0.01, 0.01), category="Retirement").start(self.RETIREMENT + 1),
        )
        self.account(
            "529",
            Account(total=60000, beta=0.6, alpha=Dist(0.01, 0.01), category="Education"),
        )

        self.account("Co-op", Account(total=720000, alpha=Dist(0.02, 0.004), category="Real Estate"))
        self.account(
            "Co-op Mortgage",
            Mortgage(balance=200000, payment=1650, rate=0.036, category="Debt").end(2044),
        )

        self.expense("Living", Expense(monthly=5600, variation=650, increase=Dist(0.03, 0.004)))
        self.expense("Healthcare", Expense(monthly=700, variation=120, increase=Dist(0.04, 0.006)))
        self.expense("Kid activities", Expense(monthly=500, variation=120, increase=Dist(0.03, 0.004)).end(2036))
        self.expense("College", Expense(annually=42000, increase=Dist(0.04, 0.004)).start(2038).end(2041))

        self.transfer("457b contribution", Transfer(annually=15000, increase=Dist(0.02, 0.0)).end(self.RETIREMENT))
        self.transfer("Roth contribution", Transfer(annually=7000, increase=Dist(0.02, 0.0)).end(self.RETIREMENT))
        self.transfer("529 contribution", Transfer(annually=6000, increase=Dist(0.02, 0.0)).end(2037))
        self.transfer("Retirement draw", Transfer(annually=30000, increase=Dist(0.02, 0.0)).start(self.RETIREMENT + 1))

    def run(self):
        gross_income = self.account("Income")
        checking = self.account("Checking")
        brokerage = self.account("Brokerage")

        acct_457b = self.account("457b")
        roth = self.account("Roth IRA")
        acct_529 = self.account("529")
        mortgage = self.account("Co-op Mortgage")

        retirement_accounts = [acct_457b, roth]
        expense_accounts = [checking, brokerage, roth]

        self.income("Teacher salary").into(gross_income)
        self.income("Summer stipend").into(gross_income)
        self.income("Pension income").into(gross_income)

        self.transfer("457b contribution").go([gross_income], acct_457b)
        self.transfer("Roth contribution").go([gross_income], roth)

        self.transfer("Retirement draw").go(retirement_accounts, gross_income)

        mortgage.interest_outof([gross_income] + expense_accounts)

        IncomeTax.federal.calculate([gross_income])
        IncomeTax.state.calculate([gross_income])
        IncomeTax.city.calculate([gross_income])

        self.transfer("529 contribution").go([gross_income] + expense_accounts, acct_529)

        IncomeTax.federal.commit()
        IncomeTax.state.commit()
        IncomeTax.city.commit()

        gross_income.into(checking)

        for exp in self.expenses.values():
            if exp.name == "College":
                exp.outof([acct_529] + expense_accounts)
            else:
                exp.outof(expense_accounts)

        mortgage.principal_outof(expense_accounts)
        checking.keep(brokerage, [brokerage], keep_max=80000, keep_min=25000)


def main():
    model = SingleParentPublicService()
    mc = MC(model, 2026, 2062)
    mc.run_once()
    mc.run(100)


if __name__ == "__main__":
    main()

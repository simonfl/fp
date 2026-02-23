#!/usr/bin/env python3

from fp_sim.sim import Model, MC
from fp_sim.util import Dist
from fp_sim.taxes import IncomeTax
from fp_sim.accounts import Income, RSU, Account, Mortgage, Expense, Transfer


class DualIncomeNycFamily(Model):
    def __init__(self):
        super().__init__()

    def setup(self):
        self.ALEX_RETIREMENT = 2045
        self.JORDAN_RETIREMENT = 2048

        self.income(
            "Alex paycheck",
            Income(annually=310000, increase=Dist(0.03, 0.01), bonus=0.12).end(self.ALEX_RETIREMENT),
        )
        self.income(
            "Jordan paycheck",
            Income(annually=210000, increase=Dist(0.03, 0.01), bonus=0.08).end(self.JORDAN_RETIREMENT),
        )

        stock_price = Account(total=55.0, beta=1.0, alpha=Dist(0.02, 0.08))
        self.income("Company stock", stock_price)
        self.income("Alex RSUs", RSU(quarterly_qty=350, price=stock_price).end(2034, 10))

        self.account("Income", Account())
        self.account("RSUs", Account())

        self.account("Checking", Account(total=140000, category="Cash"))
        self.account(
            "Taxable Brokerage",
            Account(total=1200000, basis=920000, beta=0.9, alpha=Dist(0.01, 0.02), tax_rate=0.2, category="Investments"),
        )
        self.account(
            "College 529 - Child 1",
            Account(total=150000, beta=0.6, alpha=Dist(0.01, 0.01), category="Education"),
        )
        self.account(
            "College 529 - Child 2",
            Account(total=130000, beta=0.6, alpha=Dist(0.01, 0.01), category="Education"),
        )

        self.account(
            "Alex 401k",
            Account(total=700000, beta=0.8, alpha=Dist(0.01, 0.01), category="Retirement").start(2045),
        )
        self.account(
            "Jordan 401k",
            Account(total=420000, beta=0.8, alpha=Dist(0.01, 0.01), category="Retirement").start(2048),
        )
        self.account(
            "Backdoor Roth",
            Account(total=260000, beta=0.8, alpha=Dist(0.01, 0.01), category="Retirement").start(2045),
        )

        self.account(
            "NYC Condo",
            Account(total=1800000, alpha=Dist(0.02, 0.005), category="Real Estate"),
        )
        self.account(
            "Condo Mortgage",
            Mortgage(balance=950000, payment=6500, rate=0.043, category="Debt").end(2055),
        )

        self.expense("Core living", Expense(monthly=15500, variation=1500, increase=Dist(0.03, 0.005)))
        self.expense("Private school", Expense(annually=128000, increase=Dist(0.04, 0.005)).end(2037))
        self.expense("Travel", Expense(annually=22000, variation=6000, increase=Dist(0.03, 0.01)))

        self.transfer("Alex 401k contribution", Transfer(annually=23000, increase=Dist(0.03, 0.0)).end(self.ALEX_RETIREMENT))
        self.transfer("Jordan 401k contribution", Transfer(annually=23000, increase=Dist(0.03, 0.0)).end(self.JORDAN_RETIREMENT))
        self.transfer("Backdoor Roth contribution", Transfer(annually=14000, increase=Dist(0.02, 0.0)).end(2044))
        self.transfer("College 529 child1", Transfer(annually=8000, increase=Dist(0.02, 0.0)).end(2037))
        self.transfer("College 529 child2", Transfer(annually=8000, increase=Dist(0.02, 0.0)).end(2039))

        self.transfer("Retirement draw pre-tax", Transfer(annually=180000, increase=Dist(0.025, 0.0)).start(2046))

    def run(self):
        gross_income = self.account("Income")
        gross_rsus = self.account("RSUs")

        checking = self.account("Checking")
        brokerage = self.account("Taxable Brokerage")

        alex_401k = self.account("Alex 401k")
        jordan_401k = self.account("Jordan 401k")
        roth = self.account("Backdoor Roth")

        college1 = self.account("College 529 - Child 1")
        college2 = self.account("College 529 - Child 2")

        mortgage = self.account("Condo Mortgage")

        retirement_accounts = [alex_401k, jordan_401k]
        expense_accounts = [checking, brokerage, roth]

        self.income("Alex paycheck").into(gross_income)
        self.income("Jordan paycheck").into(gross_income)
        self.income("Alex RSUs").into(gross_rsus)

        self.transfer("Alex 401k contribution").go([gross_income], alex_401k)
        self.transfer("Jordan 401k contribution").go([gross_income], jordan_401k)

        self.transfer("Retirement draw pre-tax").go(retirement_accounts, gross_income)

        mortgage.interest_outof([gross_income] + expense_accounts)

        IncomeTax.federal.calculate([gross_income, gross_rsus])
        IncomeTax.city.calculate([gross_income, gross_rsus])

        self.transfer("College 529 child1").go([gross_income] + expense_accounts, college1)
        self.transfer("College 529 child2").go([gross_income] + expense_accounts, college2)

        IncomeTax.state.calculate([gross_income, gross_rsus])

        IncomeTax.federal.commit()
        IncomeTax.state.commit()
        IncomeTax.city.commit()

        gross_income.into(checking)
        gross_rsus.into(brokerage)
        self.transfer("Backdoor Roth contribution").go([checking, brokerage], roth)

        for exp in self.expenses.values():
            if exp.name == "Private school":
                # Split school cashflow across both 529 plans first, then taxable.
                exp.outof([college1, college2] + expense_accounts)
            else:
                exp.outof(expense_accounts)

        mortgage.principal_outof(expense_accounts)
        checking.keep(brokerage, [brokerage], keep_max=200000, keep_min=75000)


def main():
    model = DualIncomeNycFamily()
    mc = MC(model, 2026, 2065)
    mc.run_once()
    mc.run(100)


if __name__ == "__main__":
    main()

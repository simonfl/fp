#!/usr/bin/env python3

from fp_sim.sim import Model, MC
from fp_sim.util import Dist
from fp_sim.taxes import IncomeTax
from fp_sim.accounts import Income, Account, Expense, Transfer


class SmallBusinessOwner(Model):
    def __init__(self):
        super().__init__()

    def setup(self):
        self.RETIREMENT = 2048

        self.income(
            "Owner salary",
            Income(annually=180000, increase=Dist(0.03, 0.015), bonus=0.2).end(self.RETIREMENT),
        )
        self.income(
            "Business distribution",
            Income(annually=140000, increase=Dist(0.04, 0.02), bonus=0.0).end(self.RETIREMENT),
        )
        self.income(
            "Rental income",
            Income(annually=30000, increase=Dist(0.02, 0.01), bonus=0.0),
        )

        self.account("Income", Account())

        self.account("Operating Cash", Account(total=180000, category="Cash"))
        self.account("Emergency Fund", Account(total=220000, category="Cash"))
        self.account(
            "Taxable Portfolio",
            Account(total=850000, basis=620000, beta=0.9, alpha=Dist(0.01, 0.02), tax_rate=0.2, category="Investments"),
        )
        self.account(
            "SEP IRA",
            Account(total=450000, beta=0.8, alpha=Dist(0.01, 0.01), category="Retirement").start(self.RETIREMENT + 1),
        )
        self.account(
            "Solo Roth 401k",
            Account(total=260000, beta=0.8, alpha=Dist(0.01, 0.01), category="Retirement").start(self.RETIREMENT + 1),
        )

        self.expense("Household", Expense(monthly=9000, variation=1200, increase=Dist(0.03, 0.005)))
        self.expense("Business overhead", Expense(monthly=3500, variation=900, increase=Dist(0.03, 0.01)))
        self.expense("Health insurance", Expense(monthly=1800, variation=150, increase=Dist(0.05, 0.005)))
        self.expense("Planned capex", Expense(annually=25000, variation=7000, increase=Dist(0.02, 0.01)))

        self.transfer("SEP contribution", Transfer(annually=25000, increase=Dist(0.03, 0.0)).end(self.RETIREMENT))
        self.transfer("Roth solo contribution", Transfer(annually=14000, increase=Dist(0.03, 0.0)).end(self.RETIREMENT))
        self.transfer("Retirement draw", Transfer(annually=170000, increase=Dist(0.02, 0.0)).start(self.RETIREMENT + 1))

    def run(self):
        gross_income = self.account("Income")

        operating_cash = self.account("Operating Cash")
        emergency = self.account("Emergency Fund")
        taxable = self.account("Taxable Portfolio")

        sep_ira = self.account("SEP IRA")
        solo_roth = self.account("Solo Roth 401k")

        savings_accounts = [emergency, taxable]
        retirement_accounts = [sep_ira, solo_roth]
        expense_accounts = [operating_cash] + savings_accounts + [solo_roth]

        self.income("Owner salary").into(gross_income)
        self.income("Business distribution").into(gross_income)
        self.income("Rental income").into(gross_income)

        self.transfer("SEP contribution").go([gross_income], sep_ira)
        self.transfer("Roth solo contribution").go([gross_income], solo_roth)
        self.transfer("Retirement draw").go(retirement_accounts, gross_income)

        IncomeTax.federal.calculate([gross_income])
        IncomeTax.state.calculate([gross_income])
        IncomeTax.city.calculate([gross_income])

        IncomeTax.federal.commit()
        IncomeTax.state.commit()
        IncomeTax.city.commit()

        gross_income.into(operating_cash)

        for exp in self.expenses.values():
            exp.outof(expense_accounts)

        operating_cash.keep(taxable, savings_accounts, keep_max=220000, keep_min=100000)
        emergency.keep(taxable, [taxable], keep_max=300000, keep_min=150000)


def main():
    model = SmallBusinessOwner()
    mc = MC(model, 2026, 2060)
    mc.run_once()
    mc.run(100)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3

from fp_sim.sim import Model, MC
from fp_sim.util import Dist
from fp_sim.taxes import IncomeTax
from fp_sim.accounts import Income, Account, Expense, Transfer


class EarlyRetireeCoastFire(Model):
    def __init__(self):
        super().__init__()

    def setup(self):
        self.RETIREMENT_START = 2032

        self.income(
            "Part-time consulting",
            Income(annually=85000, increase=Dist(0.02, 0.01), bonus=0.0),
        )
        self.income(
            "Partner part-time",
            Income(annually=50000, increase=Dist(0.02, 0.01), bonus=0.0),
        )
        self.income(
            "Rental net cashflow",
            Income(annually=28000, increase=Dist(0.02, 0.005), bonus=0.0),
        )
        self.income(
            "Social security household",
            Income(annually=58000, increase=Dist(0.02, 0.0), bonus=0.0).start(2043),
        )

        self.account("Income", Account())

        self.account("Checking", Account(total=120000, category="Cash"))
        self.account(
            "Taxable",
            Account(total=2100000, basis=1650000, beta=0.9, alpha=Dist(0.01, 0.02), tax_rate=0.2, category="Investments"),
        )
        self.account(
            "Roth IRA Household",
            Account(total=780000, beta=0.8, alpha=Dist(0.01, 0.01), category="Retirement").start(2032),
        )
        self.account(
            "Traditional IRA Household",
            Account(total=920000, beta=0.8, alpha=Dist(0.01, 0.01), category="Retirement").start(2032),
        )

        self.expense("Core living", Expense(monthly=9800, variation=900, increase=Dist(0.03, 0.004)))
        self.expense("Healthcare bridge", Expense(monthly=2400, variation=250, increase=Dist(0.05, 0.005)).end(2042))
        self.expense("Travel and hobbies", Expense(monthly=1800, variation=700, increase=Dist(0.03, 0.006)))

        self.transfer("Roth conversion style draw", Transfer(annually=45000, increase=Dist(0.02, 0.0)).start(self.RETIREMENT_START))
        self.transfer("Taxable draw", Transfer(annually=60000, increase=Dist(0.02, 0.0)).start(self.RETIREMENT_START))

    def run(self):
        gross_income = self.account("Income")

        checking = self.account("Checking")
        taxable = self.account("Taxable")
        roth = self.account("Roth IRA Household")
        trad = self.account("Traditional IRA Household")

        expense_accounts = [checking, taxable, roth]

        self.income("Part-time consulting").into(gross_income)
        self.income("Partner part-time").into(gross_income)
        self.income("Rental net cashflow").into(gross_income)
        self.income("Social security household").into(gross_income)

        self.transfer("Roth conversion style draw").go([trad], gross_income)
        self.transfer("Taxable draw").go([taxable], gross_income)

        IncomeTax.federal.calculate([gross_income])
        IncomeTax.state.calculate([gross_income])
        IncomeTax.city.calculate([gross_income])

        IncomeTax.federal.commit()
        IncomeTax.state.commit()
        IncomeTax.city.commit()

        gross_income.into(checking)

        for exp in self.expenses.values():
            exp.outof(expense_accounts)

        checking.keep(taxable, [taxable], keep_max=175000, keep_min=70000)


def main():
    model = EarlyRetireeCoastFire()
    mc = MC(model, 2026, 2058)
    mc.run_once()
    mc.run(100)


if __name__ == "__main__":
    main()


class IncomeTax(object):
	def __init__(self, name, brackets, rates):
		self.name = name
		self.brackets = brackets
		self.rates = rates
		self.taxes = []

	def tax(self, total, marginal):
		tax = 0
		taxed = total * 12
		left_to_tax = marginal * 12
		i = 0
		while left_to_tax > 0:
			if taxed < self.brackets[i]:
				amt = min(left_to_tax, self.brackets[i] - taxed)
				tax += amt * self.rates[i]
				taxed += amt
				left_to_tax -= amt
			i += 1

		return tax / 12

	def calculate(self, accounts):
		total = 0
		for acct in accounts:
			bal = acct.balance()
			self.taxes.append((acct, self.tax(total, bal)))
			total += bal

	def commit(self):
		for acct, amt in self.taxes:
			acct.withdraw(amt, self.name)
		self.taxes = []


IncomeTax.federal = IncomeTax('Federal income tax',
		[19750, 80250, 171050, 326600, 414700, 622050, 999999999],
		[0.1,    0.12,   0.22,   0.24,   0.32,   0.35,     0.37]
	)

IncomeTax.state = IncomeTax('State income tax',
		[17150, 23600,  27900, 43000, 161550, 323200, 2155350, 999999999],
		[0.04,  0.045, 0.0525, 0.059, 0.0609, 0.0641,  0.0685,   0.0882]
	)
IncomeTax.city = IncomeTax('City income tax',
		[  12000,   25000,   50000, 999999999],
		[0.03078, 0.03762, 0.03819,  0.03876]
	)


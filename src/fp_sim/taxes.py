class IncomeTax(object):
	def __init__(self, name, brackets, rates):
		self.name = name
		self.brackets = brackets
		self.rates = rates
		self.taxes = []

	def tax(self, total, marginal):
		if marginal <= 0:
			return 0
		tax = 0
		taxed = total * 12
		left_to_tax = marginal * 12
		i = 0
		while left_to_tax > 0 and i < len(self.brackets):
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

	def clear(self):
		self.taxes = []


IncomeTax.federal = IncomeTax('Federal income tax',
		# 2026 tax year, married filing jointly
		# Source: IRS Rev. Proc. 2025-32 / IR-2025-103
		[24800, 100800, 211400, 403550, 512450, 768700, 999999999],
		[0.1,    0.12,   0.22,   0.24,   0.32,   0.35,     0.37]
	)

IncomeTax.state = IncomeTax('State income tax',
	# New York State 2025 schedule, married filing jointly
	# Source: NY Form IT-201-I (2025), NYS tax rate schedule
	[17150, 23600, 27900, 161550, 323200, 2155350, 5000000, 25000000, 999999999],
	[0.04,  0.045, 0.0525, 0.055,  0.06,   0.0685,  0.0965,  0.103,    0.109]
)
IncomeTax.city = IncomeTax('City income tax',
	# New York City 2025 resident schedule, married filing jointly
	# Source: NY Form IT-201-I (2025), NYC tax rate schedule
	[21600, 45000, 90000, 999999999],
	[0.03078, 0.03762, 0.03819,  0.03876]
)


from .util import Ledger, Dist

class Base(object):
	def __init__(self):
		self.start_year = 2020
		self.start_month = 1
		self.end_year = 2100
		self.end_month = 1
		self.year = 2020
		self.month = 1
		self.name = 'flow'

	def set_name(self, n):
		self.name = n
		return self

	def update(self, year, month, market=0):
		self.year = year
		self.month = month
		self.market = market
		self._update()

	def _update(self):
		pass

	def start(self, year, month=1):
		self.start_year = year
		self.start_month = month
		return self

	def end(self, year, month=12):
		self.end_year = year
		self.end_month = month
		return self

	def onetime(self, year, month):
		self.start(year, month)
		self.end(year, month)
		return self

	def is_current(self):
		if self.year < self.start_year or (self.year == self.start_year and self.month < self.start_month):
			return False
		if self.year > self.end_year or (self.year == self.end_year and self.month > self.end_month):
			return False
		return True

	def get(self):
		return 0

	def into(self, dst, amt=None):
		bal = self.get()
		if amt is None or amt > bal:
			amt = bal
		dst.deposit(amt, self.name)	

	def outof(self, accounts):
		amt = self.get()
		for acct in accounts:
			if amt <= 0.001:
				break
			amt -= acct.withdraw(amt, self.name)
		if amt > 0:
			raise Exception('Not enough in accounts to pay ${:.2f} for {} on {}/{}'.format(self.amt, self.name, self.month, self.year))

class Account(Base):
	def __init__(self, total=0, basis=0, beta=0, alpha=None, tax_rate=0, category=None):
		super().__init__()
		self.basis = basis
		self.gain = total - basis
		self.beta = beta
		self.alpha = alpha
		self.tax_rate = tax_rate
		self.category = category
		self.ledger = []

	def __str__(self):
		out = []
		out.append('{} {} {:<30s} {:>15s} {:>15s} {:>15s}'.format(
			'Year', 'Mo', 'Note', 'Amount', 'Tax', 'Balance'))
		for item in self.ledger:
			out.append(str(item))
		return '\n'.join(out)

	def rate(self):
		if self.alpha is None:
			return 0
		return self.market * self.beta + self.alpha.get_monthly()

	def balance(self):
		return self.basis + self.gain

	def _update(self):
		amt = self.balance() * self.rate()
		self.gain += amt
		if abs(amt) > 0.001:
			self.ledger.append(Ledger(self.year, self.month, 'Gain', amt, 0, self.balance()))

	def deposit(self, amt, note):
		self.basis += amt
		if abs(amt) > 0.001:
			self.ledger.append(Ledger(self.year, self.month, note, amt, 0, self.balance()))

	def withdraw(self, amt, note):
		if not self.is_current():
			return 0
		bal = self.balance()
		if bal <= 0 or amt <= 0:
			return 0

		taxable_fraction = 0 if bal == 0 else max(0, min(1, self.gain / bal))
		effective_tax_rate = taxable_fraction * self.tax_rate
		max_net = bal * (1 - effective_tax_rate)
		amt = min(amt, max_net)
		if amt <= 0:
			return 0

		gross = amt / (1 - effective_tax_rate) if effective_tax_rate < 1 else 0
		basis_sold = gross * (1 - taxable_fraction)
		gain_sold = gross * taxable_fraction
		tax_paid = max(0, gain_sold) * self.tax_rate
		net = gross - tax_paid

		self.basis -= basis_sold
		self.gain -= gain_sold
		if abs(self.basis) < 1e-9:
			self.basis = 0
		if abs(self.gain) < 1e-9:
			self.gain = 0
		if abs(net) > 0.001:
			self.ledger.append(Ledger(self.year, self.month, note, -net, -tax_paid, self.balance()))
		return net

	def into(self, dst, amt=None):
		if not self.is_current():
			return 0
		bal = self.balance()
		if amt is None or amt > bal:
			amt = bal
		dst.deposit(amt, 'Transfer from {}'.format(self.name))
		self.withdraw(amt, 'Transfer to {}'.format(dst.name))
		return self

	def outof(self, amt, accounts):
		for acct in accounts:
			if amt <= 0.001:
				break
			actual = acct.withdraw(amt, 'Transfer to {}'.format(self.name))
			self.deposit(actual, 'Transfer from {}'.format(acct.name))
			amt -= actual

	def sweep(self, dst, keep=0):
		bal = self.balance()
		if bal > keep:
			self.into(dst, bal - keep)
		return self

	def keep(self, dst, srcs, keep_max=0, keep_min=0):
		bal = self.balance()
		if bal > keep_max:
			self.into(dst, bal - keep_max)
		elif bal < keep_min:
			for src in srcs:
				if bal > keep_min:
					break
				src.into(self, keep_min - bal)
				bal = self.balance()
		return self


class Income(Base):
	def __init__(self, annually, increase, bonus=0, bonus_month=2, every_n_month=1):
		super().__init__()
		self.annually = annually
		self.increase = increase
		self.bonus_pct = bonus
		self.bonus_month = bonus_month
		self.every_n_month = every_n_month

	def rate(self):
		return self.increase.get()

	def _update(self):
		if self.month == 1:
			self.annually += self.annually * self.rate()

	def get(self):
		if not self.is_current():
			return 0
		amt = 0
		if self.month % self.every_n_month == 0:
			amt += self.annually / (12 / self.every_n_month)
		if self.month == self.bonus_month:
			amt += self.annually * self.bonus_pct
		return amt


class RSU(Base):
	def __init__(self, quarterly_qty, price):
		"""
		price is an Account
		"""
		super().__init__()
		self.quarterly_qty = quarterly_qty
		self.price = price

	def get(self):
		if not self.is_current():
			return 0
		if self.month % 3 == 1:
			return self.quarterly_qty * self.price.balance()
		else:
			return 0


class Mortgage(Account):
	def __init__(self, balance, payment, rate, category):
		super().__init__(-balance, 0)
		self.payment = payment
		self.rate = rate
		self.category = category

	def _update(self):
		if self.is_current():
			self.interest = -self.balance() * self.rate / 12
			self.deposit(-self.interest, 'Interest')

	def interest_outof(self, accts):
		if self.is_current():
			self.outof(self.interest, accts)

	def principal_outof(self, accts):
		if self.is_current():
			self.outof(self.payment - self.interest, accts)


class Expense(Base):
	def __init__(self, monthly=None, annually=None, variation=0, increase=None):
		super().__init__()
		monthly_variation = variation
		if monthly is not None:
			self.amt = monthly
		elif annually is not None:
			self.amt = annually / 12
			monthly_variation = variation / 12
		else:
			self.amt = 0
		self.base = 1.0
		self.monthly_dist = Dist(1, 0) if self.amt == 0 else Dist(1, monthly_variation / self.amt)
		self.increase = increase

	def _update(self):
		if self.month == 1 and self.increase is not None:
			self.base += self.base * self.increase.get()

	def get(self):
		if not self.is_current():
			return 0
		return self.monthly_dist.get() * self.base * self.amt


class Transfer(Base):
	def __init__(self, annually=None, monthly=None, increase=None):
		super().__init__()
		if monthly is not None:
			self.amt = monthly
		elif annually is not None:
			self.amt = annually / 12
		else:
			self.amt = 0
		self.increase = increase

	def _update(self):
		if self.month == 1 and self.increase is not None:
			self.amt += self.amt * self.increase.get()		

	def go(self, srcs, dst):
		if self.is_current():
			dst.outof(self.amt, srcs)

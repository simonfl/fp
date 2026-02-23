import random


class Dist(object):
	def __init__(self, mean, std=0, min_value=None, max_value=None):
		self.mean = mean
		self.std = std
		self.min_value = min_value
		self.max_value = max_value

	def get(self):
		val = self.mean if self.std == 0 else random.gauss(self.mean, self.std)
		if self.min_value is not None:
			val = max(self.min_value, val)
		if self.max_value is not None:
			val = min(self.max_value, val)
		return val

	def get_monthly(self):
		annual = self.get()
		if annual <= -1:
			return -1
		return (1 + annual) ** (1 / 12.0) - 1


class Ledger(object):
	def __init__(self, year, month, note, amount, tax, balance):
		self.year = year
		self.month = month
		self.note = note
		self.amount = amount
		self.tax = tax
		self.balance = balance

	def _fmt(self, value):
		if abs(value) < 0.001:
			value = 0
		return '${:,.2f}'.format(value)

	def __str__(self):
		return '{} {} {:<30s} {:>15s} {:>15s} {:>15s}'.format(
			self.year,
			self.month,
			self.note[:30],
			self._fmt(self.amount),
			self._fmt(self.tax),
			self._fmt(self.balance),
		)

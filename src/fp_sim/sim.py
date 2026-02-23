
import random
import os
from collections import defaultdict
from .util import Dist

class Model(object):
	def __init__(self):
		self.reset()

	def reset(self):
		self.incomes = dict()
		self.expenses = dict()
		self.accounts = dict()
		self.transfers = dict()

	def run(self):
		pass

	def update(self, year, month, market):
		self.year = year
		self.month = month
		for acct in self.accounts.values():
			acct.update(year, month, market)
		for inc in self.incomes.values():
			inc.update(year, month)
		for exp in self.expenses.values():
			exp.update(year, month)
		for tr in self.transfers.values():
			tr.update(year, month)

	def income(self, name, inc=None):
		if inc is None:
			return self.incomes[name]
		self.incomes[name] = inc
		inc.set_name(name)
		return inc

	def expense(self, name, exp=None):
		if exp is None:
			return self.expenses[name]
		self.expenses[name] = exp
		exp.set_name(name)
		return exp

	def account(self, name, acct=None):
		if acct is None:
			return self.accounts[name]
		self.accounts[name] = acct
		acct.set_name(name)
		return acct

	def transfer(self, name, tr=None):
		if tr is None:
			return self.transfers[name]
		self.transfers[name] = tr
		tr.set_name(name)
		return tr

	def report(self, outdir):
		if not os.path.exists(outdir):
			os.mkdir(outdir)
		for acct in self.accounts.values():
			with open(os.path.join(outdir, acct.name), 'w') as f:
				f.write(str(acct))

class Sim(object):
	def __init__(self, model, start, end, summary_every_n_years=10, ignore_accounts=None):
		self.model = model
		self.start = start
		self.end = end
		self.ignore_accounts = ['Income', 'RSUs'] if ignore_accounts is None else ignore_accounts
		self.summary_every_n_years = summary_every_n_years
		self.summary = dict()
		

	def fmt(self, n, width=13):
		if abs(n) < 0.001:
			n = 0
		return ('{:>%ds}' % width).format('${:,.0f}'.format(n))

	def label(self, name, width=13):
		if len(name) <= width:
			return ('{:>%ds}' % width).format(name)
		return name[: width - 3] + '...'

	def accounts(self):
		return [acct for acct in self.model.accounts.values() if not acct.name in self.ignore_accounts]

	def balances(self):
		balances = [acct.balance() for acct in self.accounts()]
		total = sum(balances)
		return balances + [total]

	def run(self, quiet=False):
		market = Dist(0.1, 0.18)
		self.model.reset()
		self.model.setup()
		income_names = set(self.model.incomes.keys())
		expense_names = set(self.model.expenses.keys())

		headers = ''.join([self.label(acct.name, 13) for acct in self.accounts()])
		if not quiet:
			print(
				'Year'
				+ headers
				+ '{:>13s}{:>13s}{:>13s}{:>13s}'.format('Total', 'Income', 'Expense', 'Net')
			)

		for year in range(self.start, self.end):
			year_income = 0.0
			year_expense = 0.0
			for month in range(1, 13):
				ledger_offsets = {acct: len(acct.ledger) for acct in self.model.accounts.values()}
				self.model.update(year, month, market.get_monthly())
				self.model.run()
				for acct, offset in ledger_offsets.items():
					for item in acct.ledger[offset:]:
						if item.note in income_names and item.amount > 0:
							year_income += item.amount
						elif item.note in expense_names and item.amount < 0:
							year_expense += -item.amount

			if not quiet:
				print(
					('%d' % year)
					+ ''.join([self.fmt(bal) for bal in self.balances()])
					+ self.fmt(year_income)
					+ self.fmt(year_expense)
					+ self.fmt(year_income - year_expense)
				)

			if (year - self.start) % self.summary_every_n_years == 0:
				self.summary[year] = defaultdict(int)
				total = 0
				for acct in self.accounts():
					total += acct.balance()
					if acct.category is not None:
						self.summary[year][acct.category] += acct.balance()
					self.summary[year]['Total'] = total

		if not quiet:
			print(
				('%d' % self.end)
				+ ''.join([self.fmt(bal) for bal in self.balances()])
				+ self.fmt(0)
				+ self.fmt(0)
				+ self.fmt(0)
			)

class MC(object):
	def __init__(self, model, start, end):
		self.model = model
		self.start = start
		self.end = end

	def run_once(self):
		self._clear_tax_buffers()
		sim = Sim(self.model, self.start, self.end)
		sim.run()

	def _clear_tax_buffers(self):
		try:
			from .taxes import IncomeTax
			for tax_name in ('federal', 'state', 'city'):
				tax = getattr(IncomeTax, tax_name, None)
				if tax is not None and hasattr(tax, 'clear'):
					tax.clear()
		except Exception:
			pass

	def run(self, n, summary_every_n_years=10):
		if n <= 0:
			raise ValueError('n must be > 0')
		summary = defaultdict(lambda: defaultdict(list))
		fails = 0
		successes = 0
		last_sim = None
		for i in range(n):
			random.seed(i)
			self._clear_tax_buffers()
			sim = Sim(self.model, self.start, self.end, summary_every_n_years)
			last_sim = sim
			try:
				sim.run(True)
				successes += 1
			except Exception:
				fails += 1
				self._clear_tax_buffers()
				continue
			for year, stats in sim.summary.items():
				for key, val in stats.items():
					summary[year][key].append(val)

		if last_sim is None:
			return

		for year, stats in summary.items():
			print('\n{:>18}  {:>13} {:>13} {:>13} {:>13} {:>13}'.format(year, '10%', '20%', '50%', '80%', 'Mean'))
			for key, vals in sorted(stats.items()):
				vals = sorted(vals)
				count = len(vals)
				p10 = vals[int((count - 1) * 0.1)]
				p20 = vals[int((count - 1) * 0.2)]
				p50 = vals[int((count - 1) * 0.5)]
				p80 = vals[int((count - 1) * 0.8)]
				print('{:>18}: {} {} {} {} {}'.format(
					key, 
					last_sim.fmt(p10),
					last_sim.fmt(p20),
					last_sim.fmt(p50),
					last_sim.fmt(p80),
					last_sim.fmt(sum(vals) / count),
				))
		print('\nSuccess rate: {:.1f}%'.format(100 * successes / n))
		print('Failure rate: {:.1f}%'.format(100 * fails / n))

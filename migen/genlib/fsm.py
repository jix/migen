from collections import OrderedDict

from migen.fhdl.std import *
from migen.fhdl.module import FinalizeError
from migen.fhdl.visit import NodeTransformer

class AnonymousState:
	pass

# do not use namedtuple here as it inherits tuple
# and the latter is used elsewhere in FHDL
class NextState:
	def __init__(self, state):
		self.state = state

class _LowerNextState(NodeTransformer):
	def __init__(self, next_state_signal, encoding, aliases):
		self.next_state_signal = next_state_signal
		self.encoding = encoding
		self.aliases = aliases

	def visit_unknown(self, node):
		if isinstance(node, NextState):
			try:
				actual_state = self.aliases[node.state]
			except KeyError:
				actual_state = node.state
			return self.next_state_signal.eq(self.encoding[actual_state])
		else:
			return node

class FSM(Module):
	def __init__(self, reset_state=None):
		self.actions = OrderedDict()
		self.state_aliases = dict()
		self.reset_state = reset_state

		self.before_entering_signals = OrderedDict()
		self.before_leaving_signals = OrderedDict()
		self.after_entering_signals = OrderedDict()
		self.after_leaving_signals = OrderedDict()

	def act(self, state, *statements):
		if self.finalized:
			raise FinalizeError
		if self.reset_state is None:
			self.reset_state = state
		if state not in self.actions:
			self.actions[state] = []
		self.actions[state] += statements

	def delayed_enter(self, name, target, delay):
		if self.finalized:
			raise FinalizeError
		if delay:
			state = name
			for i in range(delay):
				if i == delay - 1:
					next_state = target
				else:
					next_state = AnonymousState()
				self.act(state, NextState(next_state))
				state = next_state
		else:
			self.state_aliases[name] = target

	def ongoing(self, state):
		is_ongoing = Signal()
		self.act(state, is_ongoing.eq(1))
		return is_ongoing

	def _get_signal(self, d, state):
		if state not in self.actions:
			self.actions[state] = []
		try:
			return d[state]
		except KeyError:
			is_el = Signal()
			d[state] = is_el
			return is_el

	def before_entering(self, state):
		return self._get_signal(self.before_entering_signals, state)

	def before_leaving(self, state):
		return self._get_signal(self.before_leaving_signals, state)

	def after_entering(self, state):
		signal = self._get_signal(self.after_entering_signals, state)
		self.sync += signal.eq(self.before_entering(state))
		return signal

	def after_leaving(self, state):
		signal = self._get_signal(self.after_leaving_signals, state)
		self.sync += signal.eq(self.before_leaving(state))
		return signal

	def do_finalize(self):
		nstates = len(self.actions)

		self.encoding = dict((s, n) for n, s in enumerate(self.actions.keys()))
		self.state = Signal(max=nstates, reset=self.encoding[self.reset_state])
		self.next_state = Signal(max=nstates)

		lns = _LowerNextState(self.next_state, self.encoding, self.state_aliases)
		cases = dict((self.encoding[k], lns.visit(v)) for k, v in self.actions.items() if v)
		self.comb += [
			self.next_state.eq(self.state),
			Case(self.state, cases).makedefault(self.encoding[self.reset_state])
		]
		self.sync += self.state.eq(self.next_state)

		# drive entering/leaving signals
		for state, signal in self.before_leaving_signals.items():
			encoded = self.encoding[state]
			self.comb += signal.eq((self.state == encoded) & ~(self.next_state == encoded))
		if self.reset_state in self.after_entering_signals:
			self.after_entering_signals[self.reset_state].reset = 1
		for state, signal in self.before_entering_signals.items():
			encoded = self.encoding[state]
			self.comb += signal.eq(~(self.state == encoded) & (self.next_state == encoded))

from BotService import BotService
import random
import time

class BotBE():

	def __init__(self):
		self.bot_svc = BotService()

	def select_random_daily_quote(self):
		quotes = self.bot_svc.get_all_quotes()
		size = len(quotes)
		if size > 0:
			random_quote_idx = random.randint(0, size - 1)
			quote_msg = quotes[random_quote_idx][2]
			quote_timestamp = quotes[random_quote_idx][1]
			return f"{quote_msg}"
		else:
			return ""

	def save_quote(self, quote):
		try:
			self.bot_svc.add_quote(quote)
			return "Agregado"
		except Exception as e:
			print(str(e))
			return "No pude hacerlo"


	def subscribe_member(self, subscribees, subscriber):
		try:
			subscribees_formatted = [str(s.id) for s in subscribees]
			self.bot_svc.subscribe_member(subscribees_formatted, subscriber)
			return "Listo ctm!"
		except Exception as e:
			print(str(e))
			return "No pude hacerlo"

	def unsubscribe_member(self, subscribees, subscriber):
		try:
			subscribees_formatted = [str(s.id) for s in subscribees]
			self.bot_svc.unsubscribe_member(subscribees_formatted, subscriber)
			return "ya"
		except Exception as e:
			print(str(e))
			return "Se fue de culo la operacion"

	def retrieve_subscribers_from_subscribee(self, subscribee):
		subscribers = [s[0] for s in self.bot_svc.get_subscribers_from_subscribee(subscribee) ]
		print(f"List of subscribers: {subscribers}") # tuple in format (id,)
		# format message containing the quotes
		return subscribers

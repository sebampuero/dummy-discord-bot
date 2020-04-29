from BotDAO import BotDAO

class BotService():
	
	def __init__(self):
		self.dao = BotDAO()
		
	def subscribe_member(self, subscribees, subscriber):
		self.dao.subscribe_member(subscribees, subscriber)

	def unsubscribe_member(self, subscribees, subscriber):
		self.dao.unsubscribe_member(subscribees, subscriber)
		
	def get_subscribers_from_subscribee(self, subscribee):
		return self.dao.get_subscribers_from_subscribee(subscribee)

	def add_quote(self, quote):
		self.dao.add_quote(quote)

	def get_all_quotes(self):
		return self.dao.get_all_quotes()

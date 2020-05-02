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

	def set_alert(self, url, price_range, currency, user_id):
		self.dao.set_alert(url, price_range, currency, user_id)
  
	def unset_alert(self, url, user_id):
		self.dao.unset_alert(url, user_id)
  
	def get_all_alerts(self):
		return self.dao.get_all_alerts()

	def update_last_checked_at_alert(self, alert_id):
		self.dao.update_last_checked_at_alert(alert_id)
  
	def delete_alert(self, alert_id):
		self.dao.delete_alert(alert_id)

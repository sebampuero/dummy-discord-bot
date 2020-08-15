from DAO.BotDAO import BotDAO
from DAO.BotDAOFile import BotDAOFile

"""
Service Layer for connecting to a DAO
"""

class BotService():
	
	def __init__(self, test_db=None):
		self.dao = BotDAO() if not test_db else BotDAO(test_db)
		self.dao_file = BotDAOFile()
		
	def subscribe_member(self, subscribees, subscriber):
		self.dao.subscribe_member(subscribees, subscriber)

	def unsubscribe_member(self, subscribees, subscriber):
		self.dao.unsubscribe_member(subscribees, subscriber)
		
	def get_subscribers_from_subscribee(self, subscribee):
		return self.dao.get_subscribers_from_subscribee(subscribee)

	def get_subscribees_from_subscriber(self, subscriber):
		return self.dao.get_subscribees_from_subscriber(subscriber)

	def set_alert(self, url, price_range, currency, user_id):
		self.dao.set_alert(url, price_range, currency, user_id)
  
	def unset_alert(self, url, user_id):
		self.dao.unset_alert(url, user_id)
  
	def get_all_alerts(self):
		return self.dao.get_all_alerts()

	def get_all_alerts_for_user(self, user_id):
		return self.dao.get_all_alerts_for_user(user_id)

	def update_last_checked_at_alert(self, alert_id):
		self.dao.update_last_checked_at_alert(alert_id)
  
	def delete_alert(self, alert_id):
		self.dao.delete_alert(alert_id)

	def get_radios(self):
		return self.dao_file.get_radios()

	def get_users_welcome_audios(self):
		return self.dao_file.get_users_welcome_audios()

	def save_radios(self, radios_new):
		self.dao_file.save_radios(radios_new)

	def save_users_welcome_audios(self, new_):
		self.dao_file.save_users_welcome_audios(new_)

	def save_playlist_for_user(self, user_id, url, name):
		self.dao.save_playlist_for_user(user_id, url, name)

	def read_playlists_for_user(self, user_id):
		return self.dao.read_playlists_for_user(user_id)

	def delete_playlist_for_user(self, user_id, playlist_name):
		return self.dao.delete_playlist_for_user(user_id, playlist_name)

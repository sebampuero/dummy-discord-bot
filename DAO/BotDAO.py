from DB.db import DB
import json

"""
The Bot Data Access Object is responsible for accessing the data stored in the DB Mysql
"""

class BotDAO():
	
	def __init__(self):
		self.db = DB()
		
	def subscribe_member(self, subscribees, subscriber):
		self.unsubscribe_member(subscribees, subscriber)
		sql = "INSERT INTO subscriptions(subscribee, subscriber) VALUES(%s, %s)"
		data = []
		for subscribee in subscribees:
			data.append((subscribee, subscriber))
		#self.db.execute_query(sql)
		self.db.execute_query_with_data(sql, data)

	def unsubscribe_member(self, to_unsubscribees, subscriber):
		formatted_str = ','.join(map(str, to_unsubscribees))
		print(formatted_str)
		print(subscriber)
		sql = f"DELETE FROM subscriptions WHERE subscribee in ({formatted_str}) AND subscriber = '{subscriber}' "
		print(sql)
		self.db.execute_query(sql)

	def get_subscribers_from_subscribee(self, subscribee):
		sql = f"SELECT subscriber FROM subscriptions WHERE subscribee = '{subscribee}'"
		return self.db.execute_query_with_result(sql)

	def add_quote(self, quote, member_id):
		sql = f"INSERT INTO quotes(timestamp, value, discord_user_id) VALUES(UNIX_TIMESTAMP(), '{quote}', '{member_id}')"
		self.db.execute_query(sql)

	def get_all_quotes(self):
		sql = "SELECT * FROM quotes"
		return self.db.execute_query_with_result(sql)

	def set_alert(self, url, price_range, currency, user_id):
		self.db.execute_query(f"DELETE FROM alerts WHERE url = '{url}' AND discord_user_id = '{user_id}'")
		sql = f"INSERT INTO alerts(url, price_limit, last_checked_at, discord_user_id, currency) VALUES('{url}', '{price_range}', UNIX_TIMESTAMP(), '{user_id}', '{currency}')"
		self.db.execute_query(sql)
  
	def unset_alert(self, url, user_id):
		sql = f"DELETE FROM alerts WHERE discord_user_id = '{user_id}' AND url = '{url}'"
		self.db.execute_query(sql)
  
	def get_all_alerts(self):
		sql = f"SELECT * FROM alerts where UNIX_TIMESTAMP() - last_checked_at > 3600"
		#sql = "SELECT * FROM alerts"
		return self.db.execute_query_with_result(sql)

	def update_last_checked_at_alert(self, alert_id):
		sql = f"UPDATE alerts SET last_checked_at = UNIX_TIMESTAMP() WHERE id = {alert_id}"
		self.db.execute_query(sql)

	def delete_alert(self, alert_id):
		sql = f"DELETE FROM alerts WHERE id = {alert_id}"
		self.db.execute_query(sql)

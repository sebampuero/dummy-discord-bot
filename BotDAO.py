from db import DB

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

	def add_quote(self, quote):
		sql = f"INSERT INTO quotes(timestamp, value) VALUES(UNIX_TIMESTAMP(), '{quote}')"
		self.db.execute_query(sql)

	def get_all_quotes(self):
		sql = "SELECT * FROM quotes"
		return self.db.execute_query_with_result(sql)

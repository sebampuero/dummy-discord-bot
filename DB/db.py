import pymysql
from Utils.LoggerSaver import *
import logging
"""
Data Persistence class for MySQL DB
"""

class MySQLDB:

	def __init__(self):
		with open("password.txt", "r") as f:
			password = f.read().strip("\n")
		self.db = pymysql.connect(host="localhost", user="sebp", password=password, database="discordb")
		self.cursor = self.db.cursor()

class MySQLTESTDB(MySQLDB):

	def __init__(self):
		self.db = pymysql.connect(host="localhost", user="root", password="test", database="discordb", port=3307)
		self.cursor = self.db.cursor()

	def rollback_transaction(self):
		self.db.rollback()

class DB():
	
	def __init__(self, test_db=None):
		mysql_db = MySQLDB() if not test_db else MySQLTESTDB()
		self.cursor = mysql_db.cursor
		self.db = mysql_db.db
		print("Connected to the Database")
			
	def execute_query(self, query):
		try:
			self.cursor.execute(query)
			self.db.commit()
		except Exception as e:
			logging.error(str(e), exc_info=True)
			LoggerSaver.save_log(f"While executing query {query}", WhatsappLogger())
			self.db.rollback()

	def execute_query_with_data(self, query, tuple_data):
		try:
			self.cursor.executemany(query, tuple_data)
			self.db.commit()
		except Exception as e:
			logging.error(str(e), exc_info=True)
			LoggerSaver.save_log(f"While executing query {query}", WhatsappLogger())
			self.db.rollback()

		
	def execute_query_with_result(self, query):
		try:
			self.cursor.execute(query)
			return self.cursor.fetchall()
		except Exception as e:
			logging.error(str(e), exc_info=True)
			LoggerSaver.save_log(f"While executing query {query}", WhatsappLogger())
			return []

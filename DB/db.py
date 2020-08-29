from pymysqlpool.pool import Pool
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
		self.pool = Pool(host="localhost", user="sebp", password=password, db="discordb", port=3306, autocommit=True)
		self.pool.init()

class MySQLTESTDB(MySQLDB):

	def __init__(self):
		self.pool = Pool(host="localhost", user="root", password="test", db="discordb", port=3307, autocommit=True)
		self.pool.init()

	def rollback_transaction(self):
		self.db.rollback()

class DB():
	
	def __init__(self, test_db=None):
		mysql_db = MySQLDB() if not test_db else test_db
		self.db = mysql_db
		print("Connected to the Database")

	def get_conn_cursor(self):
		conn = self.db.pool.get_conn()
		cursor = conn.cursor()
		return conn, cursor
			
	def execute_query(self, query):
		try:
			conn, cursor = self.get_conn_cursor()
			cursor.execute(query)
		except Exception as e:
			logging.error(str(e), exc_info=True)
			LoggerSaver.save_log(f"While executing query {query}", WhatsappLogger())
		finally:
			self.db.pool.release(conn)

	def execute_query_with_data(self, query, tuple_data):
		try:
			conn, cursor = self.get_conn_cursor()
			cursor.executemany(query, tuple_data)
		except Exception as e:
			logging.error(str(e), exc_info=True)
			LoggerSaver.save_log(f"While executing query {query}", WhatsappLogger())
			self.db.rollback()
		finally:
			self.db.pool.release(conn)

	def execute_query_with_result(self, query):
		try:
			conn, cursor = self.get_conn_cursor()
			cursor.execute(query)
			return cursor.fetchall()
		except Exception as e:
			logging.error(str(e), exc_info=True)
			LoggerSaver.save_log(f"While executing query {query}", WhatsappLogger())
			return []
		finally:
			self.db.pool.release(conn)

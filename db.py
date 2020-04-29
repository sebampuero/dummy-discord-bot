import pymysql
import os

class DB():
	
	__instance = None
	
	@staticmethod
	def get_instance():
		if DB.__instance == None:
			DB()
		return DB.__instance
	
	def __init__(self):
		if DB.__instance != None:
			raise Exception("A DB instance is already running")
		else:
			password = open("password.txt", "r").read()
			self.db = pymysql.connect("localhost", "root", password, "discordb")
			self.cursor = self.db.cursor()
			
	def execute_query(self, query):
		try:
			self.cursor.execute(query)
			self.db.commit()
		except Exception as e:
			print(str(e))
			self.db.rollback()

	def execute_query_with_data(self, query, tuple_data):
		try:
			self.cursor.executemany(query, tuple_data)
			self.db.commit()
		except Exception as e:
			print(str(e))
			self.db.rollback()

		
	def execute_query_with_result(self, query):
		try:
			self.cursor.execute(query)
			return self.cursor.fetchall()
		except Exception as e:
			print(str(e))
			return []

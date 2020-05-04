from BotService import BotService
from Soup import Soup
import random
import time
import re
import datetime

class BotBE():

	def __init__(self):
		self.bot_svc = BotService()
		self.soup = Soup()

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
		print(f"List of subscribers: {subscribers} {subscribee}") # tuple in format (id,)
		# format message containing the quotes
		return subscribers

	def set_alert(self, url, price_range, currency, user_id):
		try:
			prices = price_range.split("-")
			if len(prices) != 2:
				return "Debes definir un rango de precios, ejm: 2-5 o 2.5-5.5"
			if float(prices[0]) > float(prices[1]):
				return "El rango de precios va de menor a mayor, ejm: 2-5 y no 5-2"
			if not re.match(r"^(\d{1,2}(\.\d{1,2})?-\d{1,2}(\.\d{1,2})?)$", price_range):
				return "Has formateado mal el rango de precio. Ejemplo: 12-15 o 12.5-15.5"
			if not "www.g2a.com" in url and not "www.amazon." in url:
				return "Ese no es un link de G2A o Amazon cojudo"
			if currency != "USD" and currency != "EUR":
				return "La moneda debe ser USD o EUR"
			self.bot_svc.set_alert(url, price_range, currency, user_id)
			return f"Agregue tu alerta del item en {url} con rango de precios {price_range} y moneda {currency}"
		except Exception as e:
			print(str(e))
			return "La cague de alguna manera y no pude setear tu alarma"

	def unset_alert(self, url, user_id):
		try:
			self.bot_svc.unset_alert(url, user_id)
			return f"Listo mande a la mierda tu alarma con link {url}"
		except Exception as e:
			print(str(e))
			return "La cague, intenta despues"

	def check_alerts(self):
		try: #TODO: add last_checked_at in DB!!
			alerts = self.bot_svc.get_all_alerts()
			alerts_with_price_limits_reached = []
			for row in alerts:
				current_price = self.get_store_price_for_prefix(row[1], row[5]) # url, currency
				price_range = str(row[2])
				print(f"{datetime.datetime.now()} Current price {current_price} for {row} with range {price_range}")
				lower_ = float(price_range.split("-")[0])
				upper_ = float(price_range.split("-")[1])
				self.bot_svc.update_last_checked_at_alert(row[0])
				if current_price > lower_ and current_price < upper_:
					self.bot_svc.delete_alert(row[0])
					alerts_with_price_limits_reached.append( (row[4], row[1]) ) # user_id, url
			return alerts_with_price_limits_reached
		except Exception as e:
			print(str(e))
			return []

	def get_store_price_for_prefix(self, url, currency):
		if "www.g2a.com" in url:
			return self.soup.get_price_g2a(url, currency)
		else:
			return self.soup.get_price_amazon(url, currency)

from Services.BotService import BotService
from BE.Soup import Soup
import Constants.StringConstants as Constants
import random
import time
import re
import datetime
import logging
"""
The Bot Business Entity is responsible for the business logic of the Bot regarding tasks with the persistent storage of some functions
like Quotes, Subscriptions and Alerts. Acts as a Facade to all subsequent layers
"""

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
			member_id = quotes[random_quote_idx][3]
			guild_id = quotes[random_quote_idx][4]
			return str(quote_msg), member_id, guild_id
		else:
			return ""

	def save_quote(self, quote, member_id, guild_id):
		try:
			self.bot_svc.add_quote(quote, member_id, guild_id)
			return Constants.ADDED
		except Exception as e:
			logging.error(f"{str(e)} while saving quote", exc_info=True)
			return Constants.COULD_NOT_DO_IT


	def subscribe_member(self, subscribees, subscriber):
		try:
			subscribees_formatted = [str(s.id) for s in subscribees]
			self.bot_svc.subscribe_member(subscribees_formatted, subscriber)
			return Constants.DONE
		except Exception as e:
			logging.error(f"{str(e)} while subscribing member", exc_info=True)
			return Constants.COULD_NOT_DO_IT

	def unsubscribe_member(self, subscribees, subscriber):
		try:
			subscribees_formatted = [str(s.id) for s in subscribees]
			self.bot_svc.unsubscribe_member(subscribees_formatted, subscriber)
			return Constants.DONE
		except Exception as e:
			logging.error(f"{str(e)} while unsubscribing member", exc_info=True)
			return Constants.COULD_NOT_DO_IT

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
			logging.error(f"{str(e)}", exc_info=True)
			return Constants.COULD_NOT_DO_IT

	def unset_alert(self, url, user_id):
		try:
			self.bot_svc.unset_alert(url, user_id)
			return f"Listo mande a la mierda tu alarma con link {url}"
		except Exception as e:
			print(str(e))
			return Constants.COULD_NOT_DO_IT

	def load_radios_msg(self):
		try:
			radios = self.bot_svc.get_radios()
			msg = ""
			for key, value in radios.items():
					msg = msg + f"Ciudad: `{str(key)}` \n"
					loop = 0
					for radio in value["items"]:
						loop += 1
						msg = msg + f" `{loop}` " + radio["name"] + "\n"
			return msg
		except Exception as e:
			print(str(e))
			return ""
	
	def load_radios_config(self):
		try:
			return self.bot_svc.get_radios()
		except Exception as e:
			print(str(e))
			return {}

	def load_users_welcome_audios(self):
		try:
			return self.bot_svc.get_users_welcome_audios()
		except Exception as e:
			print(str(e))
			return {}

	def save_audio_for_user(self, filename, user_id, guild_id):
		welcome_audios = self.load_users_welcome_audios()
		try:
			welcome_audios[str(user_id)]
		except KeyError:
			welcome_audios[str(user_id)] = {
				str(guild_id): {
					"active": True,
					"audios": [
						filename
					]
				}
			}
		else:
			try:
				welcome_audios[str(user_id)][str(guild_id)]
			except KeyError:
				welcome_audios[str(user_id)][str(guild_id)] = {
					"active": True,
					"audios": [
						filename
					]
				}
			else:
				welcome_audios[str(user_id)][str(guild_id)]["audios"].append(filename)
		finally:
			self.save_users_welcome_audios(welcome_audios)

	def save_radios(self, radios_new):
		try:
			self.bot_svc.save_radios(radios_new)
		except Exception as e:
			print(str(e))

	def save_users_welcome_audios(self, new_):
		try:
			self.bot_svc.save_users_welcome_audios(new_)
		except Exception as e:
			print(str(e))

	async def check_alerts(self):
		try: 
			alerts = self.bot_svc.get_all_alerts()
			alerts_with_price_limits_reached = []
			for row in alerts:
				current_price = await self.get_store_price_for_prefix(row[1], row[5]) # url, currency
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
			logging.error(f"{str(e)}", exc_info=True)
			return []

	async def get_store_price_for_prefix(self, url, currency):
		if "www.g2a.com" in url:
			return await self.soup.get_price_g2a(url, currency)
		else:
			return await self.soup.get_price_amazon(url, currency)

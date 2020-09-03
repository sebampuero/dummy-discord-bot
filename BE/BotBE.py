from Services.BotService import BotService
from BE.Soup import Soup
from Utils.LoggerSaver import *
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

	def __init__(self, test_db=None):
		self.bot_svc = BotService() if not test_db else BotService(test_db)
		self.soup = Soup()

	def subscribe_member(self, subscribees, subscriber):
		try:
			subscribees_formatted = [str(s.id) for s in subscribees]
			self.bot_svc.subscribe_member(subscribees_formatted, subscriber)
			return Constants.DONE
		except Exception as e:
			log = f"{str(e)} while subscribing member"
			logging.error(log, exc_info=True)
			LoggerSaver.save_log(log, WhatsappLogger())
			return Constants.COULD_NOT_DO_IT

	def unsubscribe_member(self, subscribees, subscriber):
		try:
			subscribees_formatted = [str(s.id) for s in subscribees]
			self.bot_svc.unsubscribe_member(subscribees_formatted, subscriber)
			return Constants.DONE
		except Exception as e:
			log = f"{str(e)} while unsubscribing member"
			logging.error(log, exc_info=True)
			LoggerSaver.save_log(log, WhatsappLogger())
			return Constants.COULD_NOT_DO_IT

	def retrieve_subscribers_from_subscribee(self, subscribee):
		subscribers = [s['subscriber'] for s in self.bot_svc.get_subscribers_from_subscribee(subscribee) ]
		return subscribers

	def retrieve_subscribees_from_subscriber(self, subscriber):
		subscribees = [s['subscribee'] for s in self.bot_svc.get_subscribees_from_subscriber(subscriber) ]
		return subscribees

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
			logging.error(str(e), exc_info=True)
			LoggerSaver.save_log(str(e), WhatsappLogger())
			return Constants.COULD_NOT_DO_IT

	def unset_alert(self, url, user_id):
		try:
			self.bot_svc.unset_alert(url, user_id)
			return f"Listo mande a la mierda tu alarma con link {url}"
		except Exception as e:
			logging.error(str(e), exc_info=True)
			LoggerSaver.save_log(str(e), WhatsappLogger())
			return Constants.COULD_NOT_DO_IT

	def retrieve_user_alerts(self, user_id):
		alerts = self.bot_svc.get_all_alerts_for_user(user_id)
		alerts_dict = dict()
		for alert in alerts:
			alerts_dict[alert['url']] = {
				"price": alert['price_limit'],
				"currency": alert['currency']
			}
		return alerts_dict

	def load_radios_msg(self):
		try:
			return self.bot_svc.get_radios()
		except Exception as e:
			logging.error(str(e), exc_info=True)
			LoggerSaver.save_log(str(e), WhatsappLogger())
			return {}
	
	def load_radios_config(self):
		try:
			return self.bot_svc.get_radios()
		except Exception as e:
			logging.error(str(e), exc_info=True)
			LoggerSaver.save_log(str(e), WhatsappLogger())
			return {}

	def load_users_welcome_audios(self):
		try:
			return self.bot_svc.get_users_welcome_audios()
		except Exception as e:
			logging.error(str(e), exc_info=True)
			LoggerSaver.save_log(str(e), WhatsappLogger())
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

	def save_radios(self, url, city, city_big, name):
		radios_old = self.load_radios_config()
		try:
			radios_old[str(city)]["items"].append({
				"name": str(name),
				"link": str(url)
			})
		except KeyError:
			radios_old[str(city)] = {
				"city": str(city_big),
				"items": [
					{
						"name": str(name),
						"link": str(url)
					}
				]
			}
		self.bot_svc.save_radios(radios_old)

	def save_users_welcome_audios(self, new_):
		try:
			self.bot_svc.save_users_welcome_audios(new_)
		except Exception as e:
			logging.error(str(e), exc_info=True)
			LoggerSaver.save_log(str(e), WhatsappLogger())

	async def check_alerts(self):
		try: 
			alerts = self.bot_svc.get_all_alerts()
			alerts_with_price_limits_reached = []
			for row in alerts:
				current_price = await self.get_store_price_for_prefix(row['url'], row['currency'])
				price_range = str(row['price_limit'])
				logging.warning(f"Current price {current_price} for {row} with range {price_range}")
				lower_ = float(price_range.split("-")[0])
				upper_ = float(price_range.split("-")[1])
				self.bot_svc.update_last_checked_at_alert(row['id'])
				if current_price > lower_ and current_price < upper_:
					self.bot_svc.delete_alert(row['id'])
					alerts_with_price_limits_reached.append( (row['user_id'], row['url']) )
			return alerts_with_price_limits_reached
		except Exception as e:
			logging.error(str(e), exc_info=True)
			LoggerSaver.save_log(f"{str(e)}", WhatsappLogger())
			return []

	async def get_store_price_for_prefix(self, url, currency):
		if "www.g2a.com" in url:
			return await self.soup.get_price_g2a(url, currency)
		else:
			return await self.soup.get_price_amazon(url, currency)

	def read_user_playlists(self, user_id):
		try: 
			result = self.bot_svc.read_playlists_for_user(user_id)
			playlists_dict_list = [{"name": pl['name'], "url": pl['url']} for pl in result]
			return playlists_dict_list
		except Exception as e:
			log = "reading playlist"
			logging.error(log, exc_info=True)
			LoggerSaver.save_log(f"{log} {str(e)}", WhatsappLogger())
			return []

	def save_playlist_for_user(self, user_id, url, name):
		try:
			self.bot_svc.save_playlist_for_user(user_id, url, name)
			return "Agregado"
		except Exception as e:
			log = "saving playlist"
			logging.error(log, exc_info=True)
			LoggerSaver.save_log(f"{log} {str(e)}", WhatsappLogger())
			return "Se produjo un error"

	def delete_playlist_for_user(self, user_id, name):
		try:
			self.bot_svc.delete_playlist_for_user(user_id, name)
			return f"Playlist {name} eliminada"
		except Exception as e:
			log = "deleting playlist"
			logging.error(log, exc_info=True)
			LoggerSaver.save_log(f"{log} {str(e)}", WhatsappLogger())
			return "Se produjo un error"

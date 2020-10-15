from BE.BotBE import BotBE
from Utils.LoggerSaver import *
import asyncio
import Constants.StringConstants as Constants
import logging
"""
 This class is responsible for managing alert commands
"""

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class Alert():
    
    def __init__(self):
        self.bot_be = BotBE()
        
    async def handle_alert_set(self, url, price_range, currency, ctx):
        ack = self.bot_be.set_alert(str(url), str(price_range), str(currency), str(ctx.author.id))
        await ctx.send(ack)
        
    async def handle_unset_alert(self, url, ctx):
        ack = self.bot_be.unset_alert(str(url), str(ctx.author.id))
        await ctx.send(ack)

    async def handle_show_alerts(self, ctx):
        alerts_dict = self.bot_be.retrieve_user_alerts(str(ctx.author.id))
        msg = "Alertas: \n"
        for url, alert in alerts_dict.items():
            msg += f"URL: {url}\Price: {alert['price']}\nCurrency: {alert['currency']}\n"
        await ctx.send(msg)
            
    async def check_alerts(self, client):
        await client.wait_until_ready()
        while not client.is_closed():
            try:
                alerts_list = await self.bot_be.check_alerts()
                if len(alerts_list) > 0:
                    print(f"Alerts: {alerts_list}")
                    for alert in alerts_list:
                        user_id = alert[0]
                        url = alert[1]
                        a_member = await client.fetch_user(user_id)
                        dm_channel = await a_member.create_dm()
                        await dm_channel.send(f"{Constants.PRICE_ALERT_REACHED} {url} <@!{user_id}>")
                await asyncio.sleep(10)
            except Exception as e:
                logger.error(str(e), exc_info=True)
                LoggerSaver.save_log(f"While checking alert {str(e)}", WhatsappLogger())
                await asyncio.sleep(5)
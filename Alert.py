from BE.BotBE import BotBE
import asyncio
import Constants.StringConstants as Constants
"""
 This class is responsible for managing alert commands
"""

class Alert():
    
    def __init__(self):
        self.bot_be = BotBE()
        
    async def handle_alert_set(self, url, price_range, currency, ctx):
        ack = self.bot_be.set_alert(str(url), str(price_range), str(currency), str(ctx.author.id))
        await ctx.send(ack)
        
    async def handle_unset_alert(self, url, ctx):
        ack = self.bot_be.unset_alert(str(url), str(ctx.author.id))
        await ctx.send(ack)
            
    async def check_alerts(self, client, text_channel):
        await client.wait_until_ready()
        while not client.is_closed():
            try:
                alerts_list = await self.bot_be.check_alerts()
                if len(alerts_list) > 0:
                    print(f"Alerts: {alerts_list}")
                    for alert in alerts_list:
                        user_id = alert[0]
                        url = alert[1]
                        await text_channel.send(f"{Constants.PRICE_ALERT_REACHED} {url} <@!{user_id}>")
                await asyncio.sleep(10)
            except Exception as e:
                print(str(e) + " but no problem for check alerts")
                await asyncio.sleep(5)
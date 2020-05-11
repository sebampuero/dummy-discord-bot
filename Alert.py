from BE.BotBE import BotBE
import asyncio
"""
 This class is responsible for managing alert commands
"""

class Alert():
    
    def __init__(self):
        self.bot_be = BotBE()
        
    async def handleAlertSet(self, message, text_channel):
        alert_msg = message.content.split(" ")
        if len(alert_msg) == 4:
            url = alert_msg[1].strip()
            price_range = alert_msg[2].strip()
            currency = alert_msg[3].strip()
            ack = self.bot_be.set_alert(str(url), str(price_range), str(currency), str(message.author.id))
            await text_channel.send(ack)
        else:
            await text_channel.send(f"Mal formato huevon, tienes que incluir el link, rango de precios y la moneda (USD o EUR). Escribe --help")
        
    async def handleUnsetAlert(self, message, text_channel):
        alert_msg = message.content.split(" ")
        if len(alert_msg) == 2:
            url = alert_msg[1].strip()
            ack = self.bot_be.unset_alert(str(url), str(message.author.id))
            await text_channel.send(ack)
        else:
            await text_channel.send(f"Mal formateo huevon, pones -unset-alert [Link del juego en G2A]")
            
    async def checkAlerts(self, client, text_channel):
        await client.wait_until_ready()
        while not client.is_closed():
            try:
                alerts_list = await self.bot_be.check_alerts()
                if len(alerts_list) > 0:
                    print(f"Alerts: {alerts_list}")
                    for alert in alerts_list:
                        user_id = alert[0]
                        url = alert[1]
                        await text_channel.send(f"Tu juego bajó de precio!!! {url} <@!{user_id}>")
                await asyncio.sleep(10)
            except Exception as e:
                print(str(e) + " but no problem for check alerts")
                await asyncio.sleep(5)
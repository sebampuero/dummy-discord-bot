from BE.BotBE import BotBE
import asyncio
"""
 This class is responsible for handing quotes commands
"""


class Quote():
    
    def __init__(self):
        self.bot_be = BotBE()
    
    async def handleQuoteSave(self, message, text_channel):
        quote = message.content.split("-dailyquote ")[1]
        ack = self.bot_be.save_quote(quote)
        await text_channel.send(ack)
        
    async def showDailyQuote(self, client, text_channel):
        await client.wait_until_ready()
        while not client.is_closed():
            try:
                await asyncio.sleep(43200)
                quote = self.bot_be.select_random_daily_quote()
                if quote != "":
                    await text_channel.send(quote)
            except Exception as e:
                print(str(e) + " but no problem for daily quote")
                await asyncio.sleep(5)
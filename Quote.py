from BE.BotBE import BotBE
import asyncio
import random
"""
 This class is responsible for handing quotes commands
"""


class Quote():
    
    def __init__(self):
        self.bot_be = BotBE()
    
    async def handle_quote_save(self, quote, ctx):
        ack = self.bot_be.save_quote(quote, ctx.author.id, ctx.guild.id)
        await ctx.send(ack)
        
    async def show_daily_quote(self, client):
        await client.wait_until_ready()
        while not client.is_closed():
            try:
                sleep_time = random.randint(3600, 12000)
                await asyncio.sleep(sleep_time)
                quote, member_id, guild_id = self.bot_be.select_random_daily_quote()
                guild = self.client.get_guild(guild_id)
                if quote != "" and guild.system_channel:
                    await guild.system_channel.send(quote)
            except Exception as e:
                print(str(e) + " but no problem for daily quote")
                await asyncio.sleep(5)
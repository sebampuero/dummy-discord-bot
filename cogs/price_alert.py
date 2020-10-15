import discord
from discord.ext import commands

class pricealert(commands.Cog):
    '''Sets price alerts for Amazon or G2A products
    `-set-alert [Amazon or G2A link] [Price range] [Currency (USD or EUR)]`
    '''
    def __init__(self, client):
        self.client = client

    @commands.command(aliases=["sa"], name="set-alert")
    async def set_alert(self, ctx, url, price_range, currency):
        await self.client.alert.handle_alert_set(url, price_range, currency, ctx)

    @commands.command(aliases=["ua"], name="unset-alert")
    async def unset_alert(self, ctx, url):
        await self.client.alert.handle_unset_alert(url, ctx)

    @commands.command(name="alerts")
    async def show_alerts(self, ctx):
        '''Shows saved alerts
        '''
        await self.client.alert.handle_show_alerts(ctx)

def setup(client):
    client.add_cog(pricealert(client))
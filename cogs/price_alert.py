import discord
from discord.ext import commands

class pricealert(commands.Cog):
    '''Setea alerta de precios para huevadas en G2A o Amazon
    `-set-alert [link de amazon o G2A] [Rando de precios] [Moneda(EUR o USD)]`
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
        '''Muestra las alertas guardadas
        '''
        pass # should list all alerts that were saved in this format: price range, currency, url

def setup(client):
    client.add_cog(pricealert(client))
import discord
from discord.ext import commands

class quotes(commands.Cog):
    '''quotes que el bot mandará periodicamente
    '''
    def __init__(self, client):
        self.client = client

    @commands.command(aliases=["quote"], name="daily-quote")
    async def daily_quote(self, ctx, *quote):
        '''Agrega una quote usando `-quote o -daily-quote [quote]`
        '''
        await self.client.quote.handle_quote_save(' '.join(quote), ctx)


def setup(client):
    client.add_cog(quotes(client))
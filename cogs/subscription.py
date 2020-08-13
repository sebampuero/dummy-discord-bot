import discord
from discord.ext import commands


class subscription(commands.Cog):
    '''Comandos para suscribirse a alguien y recibir notificaciones
    '''
    def __init__(self, client):
        self.client = client

    @commands.command(aliases=["sub"])
    async def subscribe(self, ctx):
        '''Subscribirse a alguien para asi recibir notificaciones cuando se conecta a un canal de voz

        Ejemplo:
        ---------
        -subscribe o -sub @nombre
        '''
        if len(ctx.message.mentions) == 0:
            raise commands.BadArgument
        await self.client.subscription.handle_subscribe(ctx.message.mentions, ctx)

    @commands.command(aliases=["unsub"])
    async def unsubscribe(self, ctx):
        '''Desubscribirse a alguien para asi ya no recibir notificaciones cuando se conecta a un canal de voz

        Ejemplo:
        ---------
        -unsubscribe o -unsub @nombre
        '''
        if len(ctx.message.mentions) == 0:
            raise commands.BadArgument
        await self.client.subscription.handle_unsubscribe(ctx.message.mentions, ctx)

    @commands.command(aliases=["subs"])
    async def show_subscriptions(self, ctx):
        '''Muestra todas las subscripciones que hayas hecho
        '''
        pass


def setup(client):
    client.add_cog(subscription(client))
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

    @commands.command(aliases=["mysubs"])
    async def show_subscribers(self, ctx):
        '''Muestra todos tus suscriptores
        '''
        subscriptions = self.client.subscription.handle_show_subscriptions(ctx)
        msg = "Lista de suscritos: "
        for subscriber in subscriptions:
            member = await self.client.fetch_user(subscriber)
            if member != None:
                msg += f"{member.display_name} "
        await ctx.send(msg)

    @commands.command(aliases=["subs"])
    async def show_subscribees(self, ctx):
        '''Muestra a quienes estas suscrito
        '''
        subscribees = self.client.subscription.handle_show_subscribees(ctx)
        msg = "Lista de a quienes estas suscrito: "
        for subscribee in subscribees:
            member = await self.client.fetch_user(subscribee)
            if member != None:
                msg += f"{member.display_name} "
        await ctx.send(msg)


def setup(client):
    client.add_cog(subscription(client))
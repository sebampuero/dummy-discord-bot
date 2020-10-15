import discord
from discord.ext import commands


class subscription(commands.Cog):
    '''Subscription to other members and be notified when they join a voice channel
    '''
    def __init__(self, client):
        self.client = client

    @commands.command(aliases=["sub"])
    async def subscribe(self, ctx):
        '''Subscribe to someone to receive notifications when they connect to a voice channel

        Example:
        ---------
        -subscribe o -sub @name
        '''
        if len(ctx.message.mentions) == 0:
            raise commands.BadArgument
        await self.client.subscription.handle_subscribe(ctx.message.mentions, ctx)

    @commands.command(aliases=["unsub"])
    async def unsubscribe(self, ctx):
        '''Unsubscribe someone so they no longer receive notifications when they connect to a voice channel

        Example:
        ---------
        -unsubscribe o -unsub @name
        '''
        if len(ctx.message.mentions) == 0:
            raise commands.BadArgument
        await self.client.subscription.handle_unsubscribe(ctx.message.mentions, ctx)

    @commands.command(aliases=["mysubs"])
    async def show_subscribers(self, ctx):
        '''Shows all your subscribers
        '''
        subscriptions = self.client.subscription.handle_show_subscriptions(ctx)
        msg = "List of subscribers: "
        for subscriber in subscriptions:
            member = await self.client.fetch_user(subscriber)
            if member != None:
                msg += f"{member.display_name} "
        await ctx.send(msg)

    @commands.command(aliases=["subs"])
    async def show_subscribees(self, ctx):
        '''Shows who you are subscribed to
        '''
        subscribees = self.client.subscription.handle_show_subscribees(ctx)
        msg = "People you are subscribed to: "
        for subscribee in subscribees:
            member = await self.client.fetch_user(subscribee)
            if member != None:
                msg += f"{member.display_name} "
        await ctx.send(msg)


def setup(client):
    client.add_cog(subscription(client))
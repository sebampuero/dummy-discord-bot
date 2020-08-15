from BE.BotBE import BotBE
import Constants.StringConstants as Constants
"""
 This class is responsible for managing subscriptions commands 
"""

class Subscription():
    
    def __init__(self):
        self.bot_be = BotBE()
    
    async def handle_subscribe(self, mentions, ctx):
        subscriber = str(ctx.author.id)
        subscribees = mentions
        ack = self.bot_be.subscribe_member(subscribees, subscriber)
        await ctx.send(ack)

    async def handle_unsubscribe(self, mentions, ctx):
        subscriber = str(ctx.author.id)
        subscribees = mentions
        ack = self.bot_be.unsubscribe_member(subscribees, subscriber)
        await ctx.send(ack)

    def handle_show_subscriptions(self, ctx):
        subscriptions = self.bot_be.retrieve_subscribers_from_subscribee(str(ctx.author.id))
        return subscriptions

    def handle_show_subscribees(self, ctx):
        subscribees = self.bot_be.retrieve_subscribees_from_subscriber(str(ctx.author.id))
        return subscribees
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
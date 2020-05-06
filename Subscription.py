from BE.BotBE import BotBE

"""
 This class is responsible for managing subscriptions commands 
"""

class Subscription():
    
    def __init__(self):
        self.bot_be = BotBE()
    
    async def handleSubscribe(self, message, text_channel):
        subscriber = str(message.author.id)
        subscribees = message.mentions
        if len(subscribees) > 0:
            ack = self.bot_be.subscribe_member(subscribees, subscriber)
            await text_channel.send(ack)
        else:
            await text_channel.send("Debes taguear a alguien, animal. Escribe --help")

    async def handleUnsubscribe(self, message, text_channel):
        subscriber = str(message.author.id)
        subscribees = message.mentions
        if len(subscribees) > 0:
            ack = self.bot_be.unsubscribe_member(subscribees, subscriber)
            await text_channel.send(ack)
        else:
            await text_channel.send("Debes taguear a alguien, animal. Escribe --help")
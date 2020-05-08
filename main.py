import discord
from Voice import Voice
from Subscription import Subscription
from Alert import Alert
from Quote import Quote
from MessageProcessor import MessageProcessor
from ServerManager import ServerManager


"""
Main bot class
@author Sebastian Ampuero
@date 30.04.2020
"""

token = open("token.txt", "r").read()

client = discord.Client()  # starts the discord client.
voice = Voice()
subscription = Subscription()
quote = Quote()
alert = Alert()
server_manager = ServerManager()
message_processor = MessageProcessor(voice, subscription, quote, alert, server_manager)

@client.event  
async def on_ready():  
    print(f'We have logged in as {client.user}')  # notification of login.
    global general_text_chat
    global daxo_guild    
    daxo_guild = client.get_guild(451813158290587649) #689198522930823271
    for channel in client.get_all_channels():
        if str(channel) == "chat": #test
            general_text_chat = channel
    client.loop.create_task(server_manager.showServerStats(client, daxo_guild, general_text_chat))
    client.loop.create_task(quote.showDailyQuote(client, general_text_chat))
    client.loop.create_task(alert.checkAlerts(client, general_text_chat))
    message_processor.set_guild(daxo_guild)

@client.event
async def on_member_join(member):
    await message_processor.saluteNewMember(member, general_text_chat)

@client.event
async def on_message(message):  # event that happens per any message.
    if message.author == client.user:
        return
    await message_processor.handleAllMessages(message, general_text_chat)

@client.event
async def on_voice_state_update(member, before, after):
    global voice
    if voice.isVoiceStateValid(before, after):
        await voice.notifySubscribersUserJoinedVoiceChat(member, after, client)
        await voice.playWelcomeAudio(member, after)
        await voice.disconnectVoiceClientOnIdle()

client.run(token)  # recall my token was saved!

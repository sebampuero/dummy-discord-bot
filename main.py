import discord
import asyncio
import logging
import Constants.StringConstants as StringConstants
from Voice import Voice
from Subscription import Subscription
from Alert import Alert
from Quote import Quote
from MessageProcessor import MessageProcessor
from ServerManager import ServerManager
from Concurrent.FileDeleter import FileDeleterThread
from Concurrent.Server import Server

"""
Main bot class
@author Sebastian Ampuero
@date 30.04.2020
"""
logging.basicConfig(format='%(asctime)s %(message)s')
token = open("token.txt", "r").read()
client = discord.Client(activity=discord.Activity(type=discord.ActivityType.watching, name=StringConstants.ASS_DANI))  # starts the discord client.
voice = Voice(client)
subscription = Subscription()
quote = Quote()
alert = Alert()
server_manager = ServerManager()
message_processor = MessageProcessor(voice, subscription, quote, alert, server_manager)
server_thread = Server("FlaskServerThread")

is_first_connection = True

@client.event  
async def on_ready():  
    print(f'We have logged in as {client.user}')  # notification of login.
    global general_text_chat, daxo_guild, is_first_connection
    daxo_guild = client.get_guild(451813158290587649) #689198522930823271
    for channel in client.get_all_channels():
        if str(channel) == "chat": #test
            general_text_chat = channel
    if is_first_connection:
        init_threads()
        is_first_connection = False
    else:
        await message_processor.handleOnResumed(general_text_chat)
    client.loop.create_task(quote.showDailyQuote(client, general_text_chat))
    client.loop.create_task(alert.checkAlerts(client, general_text_chat))
    client.loop.create_task(server_manager.showServerStats(client, daxo_guild, general_text_chat))
    client.loop.create_task(measureHeartBeat())
    client.loop.create_task(deleteMp3FilesPeriodically())

async def deleteMp3FilesPeriodically():
    while True:
        if not voice.isVoiceClientPlaying():
            deleter_thread = FileDeleterThread("LoquendoDeleter", "./assets/audio/loquendo", "^\w+\.mp3$")
            deleter_thread.start()
        await asyncio.sleep(600)

async def measureHeartBeat():
    while True:
        latency = client.latency * 1000
        await asyncio.sleep(60)
        if latency > 2000:
            await general_text_chat.send(f"{StringConstants.BAD_PING} {round(latency, 2)} ms")

def init_threads():
    server_thread.setVoice(voice)
    server_thread.setGuild(daxo_guild)
    server_thread.setChatChannel(general_text_chat)
    server_thread.start()

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
    if member == client.user:
        return
    if voice.isVoiceStateValid(before, after):
        await voice.notifySubscribersUserJoinedVoiceChat(member, after, client)
        await voice.playWelcomeAudio(member, after)
        
@client.event
async def on_disconnect():
    logging.warning("Disconnected, is there internet connection?")

@client.event
async def on_connect():
    logging.warning("We are connected")

@client.event     
async def on_resumed():
    logging.warning("Resumed session")

loop = asyncio.get_event_loop()
try:
    loop.run_until_complete(client.start(token))
except KeyboardInterrupt:
    loop.run_until_complete(client.logout())
    # cancel all tasks lingering
finally:
    loop.close()
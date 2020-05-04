import discord
import random
from debounce import debounce
from BotBE import BotBE
import asyncio
import json
import datetime
#print(discord.__version__)  # check to make sure at least once you're on the right version!

"""
To rol in next update:
    - Activity when starting bot (showing version [major][minor])
    - Alert updates
"""

token = open("token.txt", "r").read()

client = discord.Client()  # starts the discord client.

bot_be = BotBE()

OPUS_LIBS = ['libopus-0.x86.dll', 'libopus-0.x64.dll', 'libopus-0.dll', 'libopus.so.0', 'libopus.0.dylib']

current_voice_client = None
welcome_audios_queue = []

async def handleSubscribe(message):
    subscriber = str(message.author.id)
    subscribees = message.mentions
    if len(subscribees) > 0:
        ack = bot_be.subscribe_member(subscribees, subscriber)
        await general_text_chat.send(ack)
    else:
        await general_text_chat.send("Debes taguear a alguien, animal. Escribe --help")

async def handleUnsubscribe(message):
    subscriber = str(message.author.id)
    subscribees = message.mentions
    if len(subscribees) > 0:
        ack = bot_be.unsubscribe_member(subscribees, subscriber)
        await general_text_chat.send(ack)
    else:
        await general_text_chat.send("Debes taguear a alguien, animal. Escribe --help")
    
async def handleQuoteSave(message):
    quote = message.content.split("-dailyquote ")[1]
    ack = bot_be.save_quote(quote)
    await general_text_chat.send(ack)

async def handleCustomMessage(message):
    if len(message.split(" ")) >= 2:
        options = ["si", "no", "tal vez", "quizas", "deja de preguntar huevadas conchadetumadre", "anda chambea"]
        random_idx = random.randint(0, len(options) - 1)
        await general_text_chat.send(f"{options[random_idx]}")
    else:
        await general_text_chat.send("Formula bien tu pregunta cojudo")
        
async def handleAlertSet(message):
    alert_msg = message.content.split(" ")
    if len(alert_msg) == 4:
        url = alert_msg[1].strip()
        price_range = alert_msg[2].strip()
        currency = alert_msg[3].strip()
        ack = bot_be.set_alert(str(url), str(price_range), str(currency), str(message.author.id))
        await general_text_chat.send(ack)
    else:
        await general_text_chat.send(f"Mal formato huevon, tienes que incluir el link, rango de precios y la moneda (USD o EUR). Escribe --help")
    
async def handleUnsetAlert(message):
    alert_msg = message.content.split(" ")
    if len(alert_msg) == 2:
        url = alert_msg[1].strip()
        ack = bot_be.unset_alert(str(url), str(message.author.id))
        await general_text_chat.send(ack)
    else:
        await general_text_chat.send(f"Mal formateo huevon, pones -unset-alert [Link del juego en G2A]")

@client.event  # event decorator/wrapper. More on decorators here: https://pythonprogramming.net/decorators-intermediate-python-tutorial/
async def on_ready():  # method expected by client. This runs once when connected
    print(f'We have logged in as {client.user}')  # notification of login.
    global general_text_chat
    global daxo_guild
    daxo_guild = client.get_guild(451813158290587649) #689198522930823271
    for channel in client.get_all_channels():
        if str(channel) == "chat": #test
            general_text_chat = channel

@client.event
async def on_member_join(member):
    global general_text_chat
    await general_text_chat.send(f"Hola {member.display_name}")

@client.event
async def on_message(message):  # event that happens per any message.
    if message.author == client.user:
        return
    global general_text_chat
    the_message = message.content.lower()
    if the_message.startswith("-subscribe"):
        await handleSubscribe(message)
    elif the_message.startswith("-unsubscribe"):
        await handleUnsubscribe(message)
    elif the_message.startswith("-dailyquote"):
        await handleQuoteSave(message)
    elif "quieres" in the_message:
        await handleCustomMessage(the_message)
    elif the_message.startswith("-set-alert"):
        await handleAlertSet(message)
    elif the_message.startswith("-unset-alert"):
        await handleUnsetAlert(message)
    elif the_message.startswith("--help"):
        await general_text_chat.send(f"```-subscribe [tag] \n-unsubscribe [tag] \n-dailyquote [quote diario] \n-set-alert [Link de juego G2A] [rango de precios objetivo] [Moneda(USD o EUR)]\n-unset-alert [Link de juego G2A]```")

@client.event
async def on_voice_state_update(member, before, after):
    if isVoiceStateValid(before, after):
        await notifySubscribersUserJoinedVoiceChat(member, after)
        await playWelcomeAudio(member, after)
        await disconnectVoiceClientOnIdle()
        
async def notifySubscribersUserJoinedVoiceChat(member, after):
    members_to_notify = bot_be.retrieve_subscribers_from_subscribee(str(member.id))
    for member_id in members_to_notify:
        a_member = await client.fetch_user(member_id)
        if a_member != None:
            dm_channel = await a_member.create_dm()
            await dm_channel.send(f"{member.display_name} ha entrado al canal {after.channel.name}")
            
async def playWelcomeAudio(member, after):
    try:
        global current_voice_client
        user_ids_to_audio_map = json.loads(open("users_audio_map.json", "r").read())
        if not str(member.id) in user_ids_to_audio_map:
            return
        audio_file_name = user_ids_to_audio_map[str(member.id)]
        load_opus_libs()
        if discord.opus.is_loaded():
            if current_voice_client == None:
                current_voice_client = await after.channel.connect()
            if current_voice_client.channel != after.channel:
                await current_voice_client.move_to(after.channel)
            if not current_voice_client.is_connected():
                current_voice_client = await after.channel.connect()
            first_audio_source = discord.FFmpegPCMAudio(audio_file_name)
            if current_voice_client.is_playing():
                welcome_audios_queue.append(first_audio_source)
                while True:
                    if not current_voice_client.is_playing():
                        audio_source = welcome_audios_queue.pop()
                        current_voice_client.play(audio_source)
                        if len(welcome_audios_queue) == 0:
                            break
            else:
                current_voice_client.play(first_audio_source)
    except Exception as e:
        print(f"{datetime.datetime.now()} {e} while welcoming user with audio")
        
async def disconnectVoiceClientOnIdle():
    global current_voice_client
    while True:
        await asyncio.sleep(30)
        if current_voice_client != None:
            if not current_voice_client.is_playing():
                await current_voice_client.disconnect()
                break
        
def load_opus_libs(opus_libs=OPUS_LIBS):
    if discord.opus.is_loaded():
        return True
    for opus_lib in opus_libs:
        try:
            discord.opus.load_opus(opus_lib)
            return
        except OSError:
            pass
        

def isVoiceStateValid(before, after):
    return after.channel != None and not before.self_deaf and not before.self_mute and not before.self_stream and not after.self_deaf and not after.self_mute and not after.self_stream

async def showServerStats():
    await client.wait_until_ready()
    global daxo_guild
    global general_text_chat
    
    while not client.is_closed():
        try:
            await asyncio.sleep(7200)
            in_activity, online, idle, offline = getReport(daxo_guild)
            await general_text_chat.send(f"```Online: {online} huevones.\nHaciendo ni mierda: {idle} huevones.\nJugando algo: {in_activity} huevones.\nOffline: {offline} huevones```")
        except Exception as e:
            print(str(e) + " but no problem for server stats")
            await asyncio.sleep(5)

async def showDailyQuote():
    await client.wait_until_ready()
    global general_text_chat
    while not client.is_closed():
        try:
            await asyncio.sleep(43200)
            quote = bot_be.select_random_daily_quote()
            if quote != "":
                await general_text_chat.send(quote)
        except Exception as e:
            print(str(e) + " but no problem for daily quote")
            await asyncio.sleep(5)

async def checkAlerts():
    await client.wait_until_ready()
    global general_text_chat
    while not client.is_closed():
        try:
            alerts_list = bot_be.check_alerts()
            if len(alerts_list) > 0:
                print(f"Alerts: {alerts_list}")
                for alert in alerts_list:
                    user_id = alert[0]
                    url = alert[1]
                    await general_text_chat.send(f"Tu juego bajó de precio!!! {url} <@!{user_id}>")
            await asyncio.sleep(10)
        except Exception as e:
            print(str(e) + " but no problem for check alerts")
            await asyncio.sleep(5)
        

def getReport(guild):
    online = 0
    idle = 0
    offline = 0
    in_activity = 0
    for m in guild.members:
        if not m.bot:
            if len(m.activities) > 0:
                for activity in m.activities:
                    if str(activity.type) == "ActivityType.playing":
                        in_activity += 1 
            elif len(m.activities) == 0 and str(m.status) != "offline":
                idle += 1
            if str(m.status) == "online":
                online += 1
            if str(m.status) == "offline":
                offline += 1
    return in_activity, online, idle, offline

client.loop.create_task(showServerStats())
client.loop.create_task(showDailyQuote())
client.loop.create_task(checkAlerts())
client.run(token)  # recall my token was saved!

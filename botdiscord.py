import discord
import random
from debounce import debounce
from BotBE import BotBE
import asyncio
#print(discord.__version__)  # check to make sure at least once you're on the right version!

token = open("token.txt", "r").read()

client = discord.Client()  # starts the discord client.

bot_be = BotBE()

async def handleSubscribe(message):
    subscriber = str(message.author.id)
    subscribees = message.mentions
    if len(subscribees) > 0:
        print(f"Subscribing {message.author} to {message.mentions}")
        ack = bot_be.subscribe_member(subscribees, subscriber)
        await general_text_chat.send(ack)
    else:
        await general_text_chat.send("Debes taguear a alguien, animal")

async def handleUnsubscribe(message):
    subscriber = str(message.author.id)
    subscribees = message.mentions
    if len(subscribees) > 0:
        print(f"Unsubscribing {message.author} to {message.mentions}")
        ack = bot_be.unsubscribe_member(subscribees, subscriber)
        await general_text_chat.send(ack)
    else:
        await general_text_chat.send("Debes taguear a alguien, animal")
    
async def handleQuoteSave(message):
    quote = message.content.split("-dailyquote ")[1]
    ack = bot_be.save_quote(quote)
    await general_text_chat.send(ack)

async def handleCustomMessage(message): #TODO: refactor to a better approach
    if len(message.split(" ")) >= 2:
        options = ["si", "no", "tal vez", "quizas"]
        random_idx = random.randint(0, len(options) - 1)
        await general_text_chat.send(f"{options[random_idx]}")
    else:
        await general_text_chat.send("Formula bien tu pregunta cojudo")

@client.event  # event decorator/wrapper. More on decorators here: https://pythonprogramming.net/decorators-intermediate-python-tutorial/
async def on_ready():  # method expected by client. This runs once when connected
    print(f'We have logged in as {client.user}')  # notification of login.
    global general_text_chat
    global daxo_guild
    daxo_guild = client.get_guild(451813158290587649)
    for channel in client.get_all_channels():
        if str(channel) == "chat":
            general_text_chat = channel
            if bot_be.select_random_daily_quote() != "":
                await channel.send(bot_be.select_random_daily_quote())


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
    elif the_message.startswith("--help"):
        await general_text_chat.send(f"```-subscribe [tag] \n-unsubscribe [tag] \n-dailyquote [quote diario]```")

@client.event
async def on_voice_state_update(member, before, after):
    print(f'{member} ---------    {before} {after}')
    global general_text_chat
    if isVoiceStateValid(before, after):
        members_to_notify = bot_be.retrieve_subscribers_from_subscribee(str(member.id))
        for member_id in members_to_notify:
            a_member = await client.fetch_user(member_id)
            if a_member != None:
                dm_channel = await a_member.create_dm()
                await dm_channel.send(f"{member.display_name} ha entrado al canal {after.channel.name}")

def isVoiceStateValid(before, after):
    return after.channel != None and not before.self_deaf and not before.self_mute and not before.self_stream and not after.self_deaf and not after.self_mute and not after.self_stream

async def showServerStats():
    await client.wait_until_ready()
    global daxo_guild
    global general_text_chat
    
    while not client.is_closed():
        try:
            in_activity, online, idle, offline = getReport(daxo_guild)
            await general_text_chat.send(f"```Online: {online} huevones.\nHaciendo ni mierda: {idle} huevones.\nJugando algo: {in_activity} huevones.\nOffline: {offline} huevones```")
            await asyncio.sleep(3600)
        except Exception as e:
            print(str(e) + " but no problem")
            await asyncio.sleep(5)

def getReport(guild):
    online = 0
    idle = 0
    offline = 0
    in_activity = 0
    for m in guild.members:
        if len(m.activities) > 0:
            for activity in m.activities:
                if str(activity.type) == "playing":
                    in_activity += 1 
        elif len(m.activities) == 0 and str(m.status) != "offline":
            idle += 1
        if str(m.status) == "online":
            online += 1
        if str(m.status) == "offline":
            offline += 1
    return in_activity, online, idle, offline

client.loop.create_task(showServerStats())
client.run(token)  # recall my token was saved!

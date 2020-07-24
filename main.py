import json
import discord
import asyncio
import logging
import os
import Constants.StringConstants as StringConstants
from Voice import Voice
from Subscription import Subscription
from Alert import Alert
from Quote import Quote
from Concurrent.Server import Server
from BE.BotBE import BotBE
from discord.ext import commands

class CustomContext(commands.Context):
    """
    This class will define several custom functions for our messaging context
    """
    async def sad_reaction(self):
        emoji = '😥'
        try:
            await self.message.add_reaction(emoji)
        except discord.HTTPException:
            pass

    async def bad_command_reaction(self):
        emoji = '❌'
        try:
            await self.message.add_reaction(emoji)
        except discord.HTTPException:
            pass

    async def good_command_reaction(self):
        emoji = '👍'
        try:
            await self.message.add_reaction(emoji)
        except discord.HTTPException:
            pass

    async def processing_command_reaction(self):
        emoji = '⏳'
        try:
            await self.message.add_reaction(emoji)
        except discord.HTTPException:
            pass

class ChismositoBot(commands.Bot):


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def start_bg_tasks(self):
        self.loop.create_task(self.alert.check_alerts(self))
        self.init_server()

    def init_server(self):
        server_thread = Server("FlaskServerThread")
        server_thread.set_voice(self.voice)
        server_thread.set_client(self)
        server_thread.start()

    async def get_context(self, message, *, cls=CustomContext):
        return await super().get_context(message, cls=cls)

    async def on_ready(self):  
        print(f'We have logged in as {self.user}')  # notification of login.
        self.voice = Voice(self)
        self.subscription = Subscription()
        self.quote = Quote()
        self.alert = Alert()
        self.bot_be = BotBE()
        self.start_bg_tasks()
        self.load_config()
        for guild in self.guilds:
            if guild.system_channel:
                await guild.system_channel.send("Volvi")

    def load_config(self):
        f = open("./config/config.json", "r")
        self.config = json.load(f)
        f.close()

    async def on_guild_join(self, guild):
        self.voice.populate_voice_managers()
    
    async def on_disconnect(self):
        logging.warning("Disconnected, is there internet connection?")

    async def on_connect(self):
        logging.warning("We are connected")
     
    async def on_resumed(self):
        logging.warning("Resumed session")

    async def on_voice_state_update(self, member, before, after):
        if member == self.user:
            return
        if self.voice.entered_voice_channel(before, after):
            await self.voice.notify_subscribers_user_joined_voice_chat(member, after.channel)
            await self.voice.play_welcome_audio(member, after.channel)


logging.basicConfig(format='%(asctime)s %(message)s')
client = ChismositoBot(command_prefix=commands.when_mentioned_or("-"),
                   description='El bot mas pendejo de todos', case_insensitive=True)
for filename in os.listdir('./cogs'):
    if filename.endswith(".py"):
        client.load_extension(f'cogs.{filename[:-3]}')
with open("token.txt", "r") as f:
    client.run(f.read())
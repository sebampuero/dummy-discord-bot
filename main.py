import json
import discord
import asyncio
import logging
import os
import Constants.StringConstants as StringConstants
from Functionalities.Voice.Voice import Voice
from Functionalities.Subscription.Subscription import Subscription
from Functionalities.Alert.Alert import Alert
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
        server_thread = Server(name="FlaskServerThread", client=self)
        server_thread.start()

    async def get_context(self, message, *, cls=CustomContext):
        return await super().get_context(message, cls=cls)

    async def on_ready(self):  
        print(f'We have logged in as {self.user}')  # notification of login.
        self.voice = Voice(self)
        self.subscription = Subscription()
        self.alert = Alert()
        self.bot_be = BotBE()
        self.start_bg_tasks()
        self.load_config()

    def load_config(self):
        with open("./config/config.json", "r") as f:
            self.config = json.load(f)

    async def on_guild_join(self, guild):
        logging.warning(f"Joined guild {guild.name} with id {guild.id}")
        self.voice.populate_voice_managers()

    async def on_guild_remove(self, guild):
        logging.warning(f"Removed from guild {guild.name} with id {guild.id}")
        self.voice.remove_guild_from_voice_manager(guild.id)

    async def on_voice_state_update(self, member, before, after):
        if member == self.user:
            return
        if self.voice.entered_voice_channel(before, after):
            await self.voice.notify_subscribers_user_joined_voice_chat(member, after.channel)
            await self.voice.play_welcome_audio(member, after.channel)


def main():
    logging.basicConfig(format='%(asctime)s %(message)s', filename="output.log", filemode="w")
    client = ChismositoBot(command_prefix=commands.when_mentioned_or("-"),
                    description='Dummy dummy bot', case_insensitive=True)
    for filename in os.listdir('./cogs'):
        if filename.endswith(".py"):
            client.load_extension(f'cogs.{filename[:-3]}')
    with open("token.txt", "r") as f:
        client.run(f.read())

if __name__ == '__main__':
    main()
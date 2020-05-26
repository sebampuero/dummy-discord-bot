import discord
import asyncio
import logging
import Constants.StringConstants as StringConstants
from Voice import Voice
from Subscription import Subscription
from Alert import Alert
from Quote import Quote
from Concurrent.Server import Server
from Utils.FileUtils import FileUtils
from discord.ext import commands
from CommandsProcessor import Commands

class CustomContext(commands.Context):
    """
    This class will define several custom functions for our messaging context
    """
    pass

class ChismositoBot(commands.Bot):


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.voice = Voice(self)
        self.subscription = Subscription()
        self.quote = Quote()
        self.alert = Alert()
        self.chat_channel = None

    def set_chat_channel(self, guild, chat_channel):
        self.chat_channel = chat_channel

    def start_bg_tasks(self):
        self.loop.create_task(self.quote.show_daily_quote(self, self.chat_channel))
        self.loop.create_task(self.alert.check_alerts(self, self.chat_channel))
        self.init_server()

    def init_server(self):
        server_thread = Server("FlaskServerThread")
        server_thread.set_voice(self.voice)
        server_thread.set_client(self)
        server_thread.set_chat_channel(self.chat_channel)
        server_thread.start()

    async def get_context(self, message, *, cls=CustomContext):
        return await super().get_context(message, cls=cls)

    async def on_ready(self):  
        print(f'We have logged in as {self.user}')  # notification of login.
        self.loop.create_task(self.deleteMp3FilesPeriodically())
        for channel in self.get_all_channels():
            if str(channel) == "chat": #test
                self.chat_channel = channel
        Commands(self, self.voice, self.subscription, self.quote, self.alert)
        self.start_bg_tasks()

    async def deleteMp3FilesPeriodically(self):
        while not self.is_closed() and not self.voice.is_voice_client_speaking():
            FileUtils.remove_files_in_dir("./assets/audio/loquendo", "^\w+\.mp3$")
            await asyncio.sleep(1200)
    
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
            await self.voice.notify_subscribers_user_joined_voice_chat(member, after.channel, self)
            await self.voice.play_welcome_audio(member, after.channel)


logging.basicConfig(format='%(asctime)s %(message)s')
token = open("token.txt", "r").read()
client = ChismositoBot(command_prefix="-")
client.run(token)
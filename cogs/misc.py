import discord
from discord.ext import commands
from Utils.LoggerSaver import *
from checks.Checks import *
from Utils.NetworkUtils import NetworkUtils
import random
import logging
import os

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class misc(commands.Cog):

    '''Comandos que no sirven para nada
    '''

    def __init__(self, client):
        self.client = client
        with open("./config/creds.json", "r") as f:
            creds = json.loads(f.read())
            self.ksoft_key = "Bearer " + creds["ksoft"]
            self.ksoft_base_url = "https://api.ksoft.si"

    @commands.command()
    async def ping(self, ctx):
        '''Latency
        '''
        voice_client_list = list(filter(lambda x: x.guild.id == ctx.guild.id, self.client.voice_clients))
        await ctx.send(f"I am {round(self.client.latency * 1000)}ms from the Discord Gateway")
        if len(voice_client_list) > 0:
            await ctx.send(f"I am {round(voice_client_list[0].average_latency * 1000)}ms from {voice_client_list[0].endpoint} voice channel")

    @commands.command(name="r")
    @is_owner()
    async def restart_bot(self, ctx):
        '''Restart the bot. Only lord papu can do it
        '''
        if len(self.client.voice_clients) != 0:
            return await ctx.send("The bot is playing audio and cannot restart now")
        os.system("systemctl restart discord-py.service")

    @commands.command(name="random-meme")
    @commands.cooldown(1.0, 3.0, commands.BucketType.guild)
    async def random_meme(self, ctx):
        '''Retrieves a random meme using KSoft.Si
        '''
        content = await NetworkUtils.get_request(f"{self.ksoft_base_url}/images/random-meme", headers={"Authorization": self.ksoft_key})
        if content:
            await ctx.send(f"{content['title']}\n{content['image_url']}")
        else:
            await ctx.send("Try again later")

    @commands.command(name="random-nsfw", aliases=['rd-nsfw', 'pornaso', 'nopor'])
    @commands.cooldown(1.0, 3.0, commands.BucketType.guild)
    async def random_nsfw(self, ctx):
        '''Retrieves a random nsfw gif using KSoft.Si
        '''
        content = await NetworkUtils.get_request(f"{self.ksoft_base_url}/images/random-nsfw?gifs=true", headers={"Authorization": self.ksoft_key})
        if content:
            if 'image_url' in content:
                await ctx.send(content['image_url'])
            else:
                await ctx.send("Porno no disponible")
        else:
            await ctx.send("Try again later")

    @commands.command(name="random-wikihow", aliases=['rd-wiki'])
    @commands.cooldown(1.0, 3.0, commands.BucketType.guild)
    async def random_wikihow(self, ctx):
        '''Retrieves a random Wikihow using KSoft.Si
        '''
        content = await NetworkUtils.get_request(f"{self.ksoft_base_url}/images/random-wikihow", headers={"Authorization": self.ksoft_key})
        if content:
            await ctx.send(f"{content['title']}\n{content['url']}")
        else:
            await ctx.send("Try again later")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.guild.system_channel:
            await member.guild.system_channel.send(f"Hello {member.display_name}, bienvenido/a a este canal de mierda")

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            message = await ctx.send("I do not have that command. Use `-help`", delete_after=5.0)
            await ctx.bad_command_reaction()
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"Try again in {round(error.retry_after, 2)} seconds")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"You need one more param for this command: {error.param}")
        elif isinstance(error, commands.UnexpectedQuoteError):
            await ctx.send(f"Do not include `\"` in your commands")
        elif isinstance(error, commands.CheckFailure):
            pass
        else:
            log = f"Error: {str(error)} of type {type(error)}"
            logging.error(log, exc_info=True)
            LoggerSaver.save_log(log, WhatsappLogger())
            await ctx.send(f"Bot says: {str(error)}")

def setup(client):
    client.add_cog(misc(client))
    client.get_command('r').hidden = True
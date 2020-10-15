import discord
from discord.ext import commands
from Utils.LoggerSaver import *
from checks.Checks import *
import random
import logging
import os

class misc(commands.Cog):

    '''Comandos que no sirven para nada
    '''

    def __init__(self, client):
        self.client = client

    @commands.command()
    async def ping(self, ctx):
        '''Latency
        '''
        voice_client_list = list(filter(lambda x: x.guild.id == ctx.guild.id, self.client.voice_clients))
        await ctx.send(f"I am {round(self.client.latency * 1000)}ms from the Gateway Discord")
        if len(voice_client_list) > 0:
            await ctx.send(f"I am {round(voice_client_list[0].average_latency * 1000)}ms from {voice_client_list[0].endpoint}")

    @commands.command(name="r")
    @is_owner()
    async def restart_bot(self, ctx):
        '''Restart the bot. Only lord papu can do it
        '''
        if len(self.client.voice_clients) != 0:
            return await ctx.send("The bot is playing audio and cannot restart now")
        os.system("systemctl restart discord-py.service")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.guild.system_channel:
            await member.guild.system_channel.send(f"Hello {member.display_name}, bienvenido/a a este canal de mierda")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.client.user:
            return

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
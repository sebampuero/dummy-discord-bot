import discord
from discord.ext import commands
from Utils.LoggerSaver import *
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
        '''A cuantos `ms` estoy del servidor de Discord
        '''
        await ctx.send(f"Estoy a {round(self.client.latency * 1000)}ms")

    @commands.command(name="r")
    async def restart_bot(self, ctx):
        '''Reinicia el bot. Unicamente el lord papu puede hacerlo
        '''
        if len(self.client.voice_clients) != 0:
            return await ctx.send("El bot esta reproduciendo audio y no puede reiniciarse ahora")
        self.client.load_config()
        if ctx.author.id == self.client.config["restarter"]["id"]:
            os.system("systemctl restart discord-py.service")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.guild.system_channel:
            await member.guild.system_channel.send(f"Hola {member.display_name}, bienvenido/a a este canal de mierda")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.client.user:
            return
        if "quieres" in message.content.lower():
            self.client.load_config()
            options = self.client.config["messages"]["quieres"]
            random_msg = random.choice(options)
            await message.channel.send(random_msg)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            message = await ctx.send("Yo no tengo ese comando registrado. Usa `-help`", delete_after=5.0)
            await ctx.bad_command_reaction()
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"Intenta denuevo en {round(error.retry_after, 2)} segundos")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Te falta un parametro a este comando: {error.param}")
        elif isinstance(error, commands.UnexpectedQuoteError):
            await ctx.send(f"No incluyas `\"` en tus comandos")
        else:
            log = f"Error: {str(error)} of type {type(error)}"
            logging.error(log, exc_info=True)
            LoggerSaver.save_log(log, WhatsappLogger())
            await ctx.send(f"El bot dice: {str(error)}")

def setup(client):
    client.add_cog(misc(client))
    client.get_command('r').hidden = True
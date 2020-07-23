import discord
from discord.ext import commands
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

    @commands.command(name="restart")
    async def restart_bot(self, ctx):
        '''Reinicia el bot. Unicamente el lord papu puede hacerlo
        '''
        if ctx.author.id == 279796600308498434:
            await ctx.send("Reiniciando...")
            os.system("systemctl restart discord-py.service")

    @commands.command(aliases=["quien", "quien-lol"])
    async def who(self, ctx, *args):
        value = random.randint(0, len(args) - 1)
        await ctx.send(args[value])

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.guild.system_channel:
            await member.guild.system_channel.send(f"Hola {member.display_name}, bienvenido a este canal de mierda")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.client.user:
            return
        if "quieres" in message.content.lower():
            self.client.load_config()
            options = self.client.config["messages"]["quieres"]
            random_idx = random.randint(0, len(options) - 1)
            await message.channel.send(f"{options[random_idx]}")
        elif "buenas noches" == message.content.lower():
            await message.channel.send("Usa ahora `-say buenas noches`")

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
            logging.error(f"Error: {str(error)} of type {type(error)}", exc_info=True)

def setup(client):
    client.add_cog(misc(client))
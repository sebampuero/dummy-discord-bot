import discord
from discord.ext import commands
import random
import logging

class misc(commands.Cog):

    '''Comandos que no sirven para nada
    '''

    def __init__(self, client):
        self.client = client

    @commands.command(name="set-chat")
    async def set_common_chat_channel(self, ctx, id: int):
        channel = self.client.get_channel(id)
        if channel:
            self.client.set_chat_channel(ctx.guild, channel)
        else:
            await ctx.send("Ese canal de texto no existe en el server")

    @commands.command()
    async def ping(self, ctx):
        '''A cuantos `ms` estoy del servidor de Discord
        '''
        await ctx.send(f"Estoy a {round(self.client.latency * 1000)}ms")

    @commands.command(aliases=["quien", "quien-lol"])
    async def who(self, ctx, *args):
        value = random.randint(0, len(args) - 1)
        await ctx.send(args[value])

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild_id = member.guild.id
        common_text_channel = self.client.guild_to_common_chat_map[guild_id]
        await common_text_channel.send(f"Hola {member.display_name}, bienvenido a este canal de mierda")

    @commands.Cog.listener()
    async def on_message(self, message):
        if "quieres" in message.content.lower():
            options = ["si", "no", "tal vez", "deja de preguntar huevadas conchadetumadre", "anda chambea", "estas cagado del cerebro", "obvio", "si pe webon"]
            random_idx = random.randint(0, len(options) - 1)
            await message.channel.send(f"{options[random_idx]}")
        elif "buenas noches" == message.content.lower():
            await self.client.voice.say_good_night(message.author)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            message = await ctx.send(f"Yo no tengo ese comando registrado `{ctx.message.content}`. Usa `-help`")
            await ctx.bad_command_reaction()
        else:
            logging.error(str(error), exc_info=True)
                
    

def setup(client):
    client.add_cog(misc(client))
    client.get_command('set-chat').hidden = True
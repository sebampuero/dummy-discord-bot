import discord
from discord.ext import commands
from discord import File
from ttt_imager import Imager

class games(commands.Cog):
    '''Para juegos
    '''
    def __init__(self, client):
        self.client = client

    #@commands.command(name="image")
    #async def test_cmd(self, ctx):
    #    await ctx.send(file=File(Imager(ctx.guild.id).create_initial_board()))

def setup(client):
    client.add_cog(games(client))
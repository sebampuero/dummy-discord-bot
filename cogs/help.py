import discord
from discord.ext import commands


class HelpCommand(commands.MinimalHelpCommand):
    def get_command_signature(self, command):
        return '{0.clean_prefix}{1.qualified_name} {1.signature}'.format(self, command)

    def command_not_found(self, cmd):
        return f"El comando {cmd} no existe, huevonazo"

    def get_opening_note(self):
        return "`-help [comando]` para saber de un comando. Ejemplo: `-help sayf2`\n`-help [categoria]` para saber de la categoria"

class Help(commands.Cog):

    def __init__(self, client):
        self._original_help_command = client.help_command
        client.help_command = HelpCommand()
        client.help_command.cog = self

    def cog_unload(self):
        self.client.help_command = self._original_help_command

def setup(client):
    client.add_cog(Help(client))
    client.get_command('help').hidden = True
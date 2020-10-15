import discord
from discord.ext import commands
from embeds.custom import HelpEmbed

class HelpCommand(commands.MinimalHelpCommand):

    def set_client(self, client):
        self.client = client

    def get_command_signature(self, command):
        return '{0.clean_prefix}{1.qualified_name} {1.signature}'.format(self, command)

    def command_not_found(self, cmd):
        return f"Command {cmd} does not exist, huevonazo"

    def get_opening_note(self):
        return "For info about a command, type `-help comando`.\nFor a category, type `-help category`"

    async def send_bot_help(self, mapping):
        functionalities = [
            "Play music from spotify (playlists), soundcloud and youtube. For that use the command `-metele`\n",
            "Play text with voice in several languages, for that use the command `-say`\n",
            "Game of tic-tac-toe against AI or against another cause, for that use the command `-challenge`\n",
            "Save spotify playlists under proper name, for that use the command `-playl save`. For more info `-help playl`\n",
            "View songs that are currently playing, for that use `-list l number_of_page`. For more info `-help list l`\n",
            "Save favorites to play in list later. For that `-help fav`\n",
            "Apply crazy effects on the songs that are playing `-help voice`\n",
            "Put up price alerts from sites like Amazon or G2A. For that use the command `-set-alert`\n",
            "Subscribe to other members and receive notifications when they connect to voice, for that `-subscribe`\n"
        ]
        help_embed = {
            'title': f'List of commands and categories. There are {len(list(mapping.keys())) - 2} categories.',   
            'description': 'To know more about a command, type `-help command`',
            'fields' : [],
            'footer': {
                'text': f'Currently the bot has the following functionalities:\n {"".join(functionalities)}'
            }
        }
        for cog, commands in mapping.items():
            if cog and not cog.qualified_name == "Help":
                field = dict()
                field["name"] = cog.qualified_name
                commands_str = ""
                for command in commands:
                    if not command.hidden:
                        commands_str += f"-{command} \n"
                field["value"] = commands_str
                field["inline"] = True
                help_embed["fields"].append(field)
        await self.get_destination().send(embed=HelpEmbed.from_dict(help_embed))
        return super().send_bot_help(mapping)

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
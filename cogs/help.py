import discord
from discord.ext import commands
from embeds.custom import HelpEmbed

class HelpCommand(commands.MinimalHelpCommand):

    def set_client(self, client):
        self.client = client

    def get_command_signature(self, command):
        return '{0.clean_prefix}{1.qualified_name} {1.signature}'.format(self, command)

    def command_not_found(self, cmd):
        return f"El comando {cmd} no existe, huevonazo"

    def get_opening_note(self):
        return "Para saber que hace un comando, escribe `-help comando`.\nPara saber de una categoria, `-help categoria`"

    async def send_bot_help(self, mapping):
        functionalities = [
            "Reproducir musica de spotify (playlists), soundcloud y youtube. Para eso usar el comando `-metele`\n",
            "Reproducir texto con voz en varios idiomas, para eso usar el comando `-say`\n",
            "Juego de tres en raya contra la AI o contra otro causa, para eso usar el comando `-challenge`\n",
            "Guardar playlists de spotify bajo nombre propio, para eso usar el comando `-playl save`. Para mas info `-help playl`\n",
            "Visualizar canciones que se estan reproduciendo actualmente, para eso usar `-list l numero_de_pagina`. Para mas info `-help list l`\n",
            "Poner alertas de precios de sitios como Amazon o G2A. Para eso usar el comando `-set-alert`\n",
            "Suscribirte a otros causas y recibir notificaciones cuando se conecten a voz, para eso `-subscribe`\n"
        ]
        help_embed = {
            'title': f'Lista de comandos y categorias por comandos. Hay {len(list(mapping.keys())) - 2} categorias.',   
            'description': 'Para saber mas de un comando, escribe `-help comando`',
            'fields' : [],
            'footer': {
                'text': f'Actualmente el bot tiene las siguientes funcionalidades:\n {"".join(functionalities)}'
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
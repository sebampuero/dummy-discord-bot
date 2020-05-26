from discord.ext import commands
from BE.BotBE import BotBE
from Utils.NetworkUtils import NetworkUtils
from Concurrent.Server import Server
import Constants.StringConstants as StringConstants
import logging
import random

class Commands:

    def __init__(self, client, voice, subscription, quote, alert):
        self._start_commands(BotBE(), client, voice, subscription, quote, alert)
        
    def _start_commands(self, bot_be, client, voice, subscription, quote, alert):

        @client.event
        async def on_command_error(ctx, error):
            if isinstance(error, commands.BadArgument) or isinstance(error, commands.MissingRequiredArgument):
                await ctx.send("Formateaste mal tu mensaje. Escribe `--help`")
            elif isinstance(error, commands.CommandNotFound):
                await _help(ctx)
            else:
                logging.error(str(error), exc_info=True)

        @client.command(aliases=["sub"])
        async def subscribe(ctx, *args):
            if len(args) == 0:
                raise commands.BadArgument
            await subscription.handle_subscribe(ctx.message.mentions, ctx)

        @client.command(aliases=["unsub"])
        async def unsubscribe(ctx, *args):
            if len(args) == 0:
                raise commands.BadArgument
            await subscription.handle_unsubscribe(ctx.message.mentions, ctx)
            
        @client.command(aliases=["daily-quote", "quote"])
        async def daily_quote(ctx, quote):
            await quote.handle_quote_save(quote, ctx)

        @client.command(aliases=["set-alert", "sa"])
        async def set_alert(ctx, url, price_range, currency):
            await alert.handle_alert_set(url, price_range, currency, ctx)

        @client.command(aliases=["unset-alert", "ua"])
        async def unset_alert(ctx, url):
            await alert.handle_unset_alert(url, ctx)

        @client.command(aliases=["-help", "/h"])
        async def _help(ctx):
            return await ctx.send("`-subscribe o -sub [tag]` 'Subscribirse a un webon para cuando entre a discord'\n" + 
                                    "`-unsubscribe o -unsub [tag]` 'Desuscribirse'\n" +
                                    "`-daily-quote o -quote [quote diario]` 'Mensaje diario del bot'\n" +
                                    "`-set-alert o -sa [Link de juego G2A o item de amazon] [rango de precios objetivo] [Moneda(USD o EUR)]` 'Alerta de precios en amazon o G2A'\n" +
                                    "`-unset-alert o -ua [Link de juego G2A o item de amazon]`\n" +
                                    "`-audio-off o -off`  'Desactiva tu saludo'\n" +
                                    "`-audio-on o -on` 'Activa tu saludo'\n" +
                                    '`-say o -di o -dilo-mierda "[texto a decir]" [f] o [f2] (opcional)`\n' +
                                    "`-start-radio o -sr [ciudad] [id de radio]`\n" +
                                    "`-show-radios o -radios` 'Muestra las radios disponibles'\n" +
                                    "`-stop-radio o -st`\n")

        @client.command(aliases=["off", "audio-off"])
        async def audio_off(ctx):
            await voice.deactivate_welcome_audio(ctx)

        @client.command(aliases=["on", "audio-on"])
        async def audio_on(ctx):
            await voice.activate_welcome_audio(ctx)

        @client.command(aliases=["di", "dilo-mierda"])
        async def say(ctx, text, loquendo_voice=None):
            if await _check_voice_status_invalid(ctx):
                return
            network_utils = NetworkUtils()
            audio_filename = ""
            if loquendo_voice == "f":
                audio_filename = await network_utils.get_loquendo_voice(text, voice="Monica")
            elif loquendo_voice == "f2":
                audio_filename = await network_utils.get_loquendo_voice(text, voice="Marisol")
            elif not loquendo_voice:
                audio_filename = await network_utils.get_loquendo_voice(text, voice="Jorge")
            else:
                await ctx.send('Lo que digas ahora lo pones entre " " webon')
            if audio_filename != "":
                await voice.reproduce_from_file(ctx.author, audio_filename)
            else:
                await ctx.send(StringConstants.SMTH_FUCKED_UP)

        @client.command(aliases=["show-radios", "radios"])
        async def show_radios(ctx):
            radios = bot_be.load_radios_msg()
            await ctx.send(radios)

        @client.command(aliases=["start-radio", "sr"])
        async def start_radio(ctx, city, radio_id):
            if not await _check_voice_status_invalid(ctx):
                if voice.is_voice_client_playing():
                    voice.stop_player()
                radios = bot_be.load_radios_config()
                selected_city = radios[city]
                selected_radio_url = selected_city["items"][int(radio_id) - 1]["link"]
                selected_radio_name = selected_city['items'][int(radio_id) - 1]['name']
                await voice.play_streaming(selected_radio_url, ctx, selected_radio_name)

        async def _check_voice_status_invalid(ctx):
            if not ctx.author.voice:
                await ctx.send(StringConstants.NOT_IN_VOICE_CHANNEL_MSG)
                return True
            if voice.is_voice_client_speaking():
                await ctx.send("Ahora no, cojudo")
                return True
            return False

        @client.command(aliases=["stop-radio", "st", "vete-mierda"])
        async def stop_radio(ctx):
            await ctx.send(":C")
            await voice.disconnect()

        @client.command(aliases=["adios"])
        async def good_night(ctx):
            if not await _check_voice_status_invalid(ctx):
                await voice.say_good_night(ctx.author)

        @client.command(name="set-chat")
        async def set_common_chat_channel(ctx, id: int):
            channel = client.get_channel(id)
            if channel:
                client.set_chat_channel(ctx.guild, channel)
            else:
                await ctx.send("Ese canal de texto no existe en el server")

        @client.command()
        async def ping(ctx):
            await ctx.send(f"Estoy a {round(client.latency * 1000)}ms")

        @client.command(aliases=["quien", "quien-lol"])
        async def who(ctx, *args):
            value = random.randint(0, len(args) - 1)
            await ctx.send(args[value])
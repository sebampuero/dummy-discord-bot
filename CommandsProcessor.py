from discord.ext import commands
from BE.BotBE import BotBE
from Utils.NetworkUtils import NetworkUtils
from Concurrent.Server import Server
import Constants.StringConstants as StringConstants
import logging
import random

class Commands(commands.Cog):

    def __init__(self, client, voice, subscription, quote, alert):
        self.client = client
        self.voice = voice
        self.subscription = subscription
        self.quote = quote
        self.alert = alert
        self.bot_be = BotBE()
        
    @commands.Cog.listener()
    async def on_message(self, message):
        if "quieres" in message.content.lower():
            options = ["si", "no", "tal vez", "deja de preguntar huevadas conchadetumadre", "anda chambea", "estas cagado del cerebro", "obvio", "si pe webon"]
            random_idx = random.randint(0, len(options) - 1)
            await message.channel.send(f"{options[random_idx]}")
            await self.client.process_commands(message)
        elif "buenas noches" == message.content.lower():
            if not await self._check_voice_status_invalid(message):
                await self.voice.say_good_night(message.author)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild_id = member.guild.id
        common_text_channel = self.client.guild_to_common_chat_map[guild_id]
        await common_text_channel.send(f"Hola {member.display_name}, bienvenido a este canal de mierda")

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.BadArgument) or isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Formateaste mal tu mensaje. Escribe `--help`")
        elif isinstance(error, commands.CommandNotFound):
            await self._help(ctx)
        else:
            logging.error(str(error), exc_info=True)

    @commands.command(aliases=["sub"])
    async def subscribe(self, ctx):
        if len(ctx.message.mentions) == 0:
            raise commands.BadArgument
        await self.subscription.handle_subscribe(ctx.message.mentions, ctx)

    @commands.command(aliases=["unsub"])
    async def unsubscribe(self, ctx):
        if len(ctx.message.mentions) == 0:
            raise commands.BadArgument
        await self.subscription.handle_unsubscribe(ctx.message.mentions, ctx)
        
    @commands.command(aliases=["daily-quote", "quote"])
    async def daily_quote(self, ctx, quote):
        await self.quote.handle_quote_save(quote, ctx)

    @commands.command(aliases=["set-alert", "sa"])
    async def set_alert(self, ctx, url, price_range, currency):
        await self.alert.handle_alert_set(url, price_range, currency, ctx)

    @commands.command(aliases=["unset-alert", "ua"])
    async def unset_alert(self, ctx, url):
        await self.alert.handle_unset_alert(url, ctx)

    @commands.command(aliases=["-help", "/h"])
    async def _help(self, ctx):
        return await ctx.send("-Subscribirse a un webon para cuando entre a discord `-subscribe o -sub [@nombre]`\n" + 
                                "-Desuscribirse `-unsubscribe o -unsub [@nombre]`\n" +
                                "-Mensaje diario del bot `-daily-quote o -quote [quote diario]`\n" +
                                "-Alerta de precios en amazon o G2A `-set-alert o -sa [Link de juego G2A o item de amazon] [rango de precios objetivo] [Moneda(USD o EUR)]`\n" +
                                "-Desactivar alerta `-unset-alert o -ua [Link de juego G2A o item de amazon]`\n" +
                                "-Desactiva tu saludo `-audio-off o -off`\n" +
                                "-Activa tu saludo `-audio-on o -on`\n" +
                                '-El bot dice `-say o -di o -dilo-mierda "[texto a decir]" [f] (opcional) o [f2] (opcional)`\n' +
                                "-Iniciar o cambiar de radio `-start-radio o -sr [ciudad] [id de radio]`\n" +
                                "-Muestra las radios disponibles `-show-radios o -radios`\n" +
                                "-Volumen de 0 al 100% `-volumen [%]`\n" +
                                "-Parar la radio `-stop-radio o -st`\n")

    @commands.command(aliases=["off", "audio-off"])
    async def audio_off(self, ctx):
        await self.voice.deactivate_welcome_audio(ctx)

    @commands.command(aliases=["on", "audio-on"])
    async def audio_on(self, ctx):
        await self.voice.activate_welcome_audio(ctx)

    @commands.command(aliases=["di", "dilo-mierda"])
    async def say(self, ctx, text, loquendo_voice=None):
        if await self._check_voice_status_invalid(ctx):
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
            return await ctx.send('Lo que digas ahora lo pones entre " " webon. `-say " " `')
        if audio_filename != "":
            await self.voice.reproduce_from_file(ctx.author, audio_filename)
        else:
            await ctx.send(StringConstants.SMTH_FUCKED_UP)

    @commands.command(aliases=["show-radios", "radios"])
    async def show_radios(self, ctx):
        radios = self.bot_be.load_radios_msg()
        await ctx.send(radios)

    @commands.command(aliases=["start-radio", "sr"])
    async def start_radio(self, ctx, city, radio_id):
        if not await self._check_voice_status_invalid(ctx):
            if self.voice.is_voice_playing_for_guild(ctx.guild):
                self.voice.stop_player_for_guild(ctx.guild)
            try:
                radios = self.bot_be.load_radios_config()
                selected_city = radios[city]
                selected_radio_url = selected_city["items"][int(radio_id) - 1]["link"]
                selected_radio_name = selected_city['items'][int(radio_id) - 1]['name']
                await self.voice.play_streaming(selected_radio_url, ctx, selected_radio_name)
            except IndexError:
                await ctx.send("Escribe bien cojudo, usa `-radios`")

    async def _check_voice_status_invalid(self, ctx):
        if not ctx.author.voice:
            await ctx.send(StringConstants.NOT_IN_VOICE_CHANNEL_MSG)
            return True
        if self.voice.is_voice_speaking_for_guild(ctx.guild):
            await ctx.send("Ahora no, cojudo")
            return True
        return False

    @commands.command(aliases=["stop-radio", "st", "vete-mierda", "stop"])
    async def stop_radio(self, ctx):
        await ctx.send(":C")
        await self.voice.disconnect_player_for_guild(ctx.guild)

    @commands.command(name="set-chat")
    async def set_common_chat_channel(self, ctx, id: int):
        channel = self.client.get_channel(id)
        if channel:
            self.client.set_chat_channel(ctx.guild, channel)
        else:
            await ctx.send("Ese canal de texto no existe en el server")

    @commands.command()
    async def ping(self, ctx):
        await ctx.send(f"Estoy a {round(self.client.latency * 1000)}ms")

    @commands.command(aliases=["quien", "quien-lol"])
    async def who(self, ctx, *args):
        value = random.randint(0, len(args) - 1)
        await ctx.send(args[value])

    @commands.command(aliases=["volumen", "v"])
    async def set_voice_volume(self, ctx, volume: float):
        if not ctx.author.voice:
            return
        if volume < 0 or volume > 100:
            return await ctx.send("No seas pendejo")
        await ctx.send(f"Volumen seteado al {volume}%")
        self.voice.set_volume_for_guild(volume, ctx.guild)

    @commands.command(aliases=["play", "next"])
    async def prevent_conflict(self, ctx):
        pass

        
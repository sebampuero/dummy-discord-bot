import discord
from discord.ext import commands
import Constants.StringConstants as StringConstants
from Utils.NetworkUtils import NetworkUtils
from embeds.custom import VoiceEmbeds

class voice(commands.Cog):
    '''Todo lo necesario para hacer que el bot hable y reproduzca musiquita
    '''
    def __init__(self, client):
        self.client = client

    @commands.command(aliases=["off"], name="audio-off")
    async def audio_off(self, ctx):
        '''Desactiva tu saludo personal
        '''
        await self.client.voice.deactivate_welcome_audio(ctx)

    @commands.command(aliases=["on"], name="audio-on")
    async def audio_on(self, ctx):
        '''Activa tu saludo personal
        '''
        await self.client.voice.activate_welcome_audio(ctx)

    async def execute_voice_handling(self, ctx, voice, text):
        if await self._check_voice_status_invalid(ctx):
            return
        network_utils = NetworkUtils()
        audio_filename = ""
        audio_filename = await network_utils.get_loquendo_voice(str(text), voice=voice)
        if audio_filename != "":
            await self.client.voice.reproduce_from_file(ctx.author, audio_filename)
        else:
            await ctx.send(StringConstants.SMTH_FUCKED_UP)

    @commands.command(name="say")
    async def say(self, ctx, *, text):
        '''Lo que diga el bot con voz hombre
        '''
        await self.execute_voice_handling(ctx, "Jorge", text)

    @commands.command(name="sayf")
    async def say_f(self, ctx, *, text):
        '''Lo que diga el bot con voz de flaquita
        '''
        await self.execute_voice_handling(ctx, "Monica", text)
        
    @commands.command(name="sayf2")
    async def say_f2(self, ctx, *, text):
        '''Lo que diga el bot con voz de flaquita
        '''
        await self.execute_voice_handling(ctx, "Marisol", text)
        
    @commands.command(aliases=["radios"], name="show-radios")
    async def show_radios(self, ctx):
        '''Muestra todas las radios disponibles
        '''
        radios = self.client.bot_be.load_radios_msg()
        await ctx.send(radios)

    @commands.command(aliases=["sr"], name="start-radio")
    async def start_radio(self, ctx, city, radio_id):
        '''Inicia la radio con la ciudad y su radio correspondiente
        `-start-radio o -sr [ciudad] [numero de radio]`
        '''
        if not await self._check_voice_status_invalid(ctx):
            if self.client.voice.is_voice_playing_for_guild(ctx.guild):
                self.client.voice.stop_player_for_guild(ctx.guild)
            try:
                radios = self.client.bot_be.load_radios_config()
                selected_city = radios[city]
                selected_radio_url = selected_city["items"][int(radio_id) - 1]["link"]
                selected_radio_name = selected_city['items'][int(radio_id) - 1]['name']
                await self.client.voice.play_streaming(selected_radio_url, ctx, selected_radio_name)
            except IndexError:
                await ctx.send("Escribe bien cojudo, usa `-radios`")

    async def _check_voice_status_invalid(self, ctx):
        if not ctx.author.voice:
            await ctx.send(StringConstants.NOT_IN_VOICE_CHANNEL_MSG)
            return True
        if self.client.voice.is_voice_speaking_for_guild(ctx.guild):
            await ctx.send("Ahora no, cojudo")
            return True
        return False

    @commands.command(aliases=["st", "vete-mierda", "stop"], name="stop-radio")
    async def stop_radio(self, ctx):
        '''Para la radio y bota al bot del canal
        '''
        await ctx.sad_reaction()
        await self.client.voice.disconnect_player_for_guild(ctx.guild)

    @commands.command(name="metele", aliases=["dale", "entrale", "reproduce", "hazme-la-taba"])
    async def play_youtube(self, ctx, *query):
        '''Reproduce queries y links de youtube
        '''
        if not await self._check_voice_status_invalid(ctx):
            if not query: # validate that this is an url
                return await ctx.message.add_reaction('❌')
            try:
                await ctx.message.delete()
            except:
                pass
            await self.client.voice.play_for_youtube(query, ctx)
            embed_options = {'title': f'Agregando a lista de reproduccion con busqueda: {" ".join(query)}'}
            embed = VoiceEmbeds(author=ctx.author, **embed_options)
            await ctx.send(embed=embed, delete_after=5.0)
                

    @commands.command(aliases=["v"], name="volumen")
    async def set_voice_volume(self, ctx, volume: float):
        '''Setea el volumen a un %
        `-volumen [0-100]`'''
        if not ctx.author.voice:
            return
        if volume < 0 or volume > 100:
            return await ctx.send("No seas pendejo")
        await ctx.send(f"Volumen seteado al {volume}%")
        self.client.voice.set_volume_for_guild(volume, ctx.guild)

def setup(client):
    client.add_cog(voice(client))
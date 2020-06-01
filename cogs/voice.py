import discord
from discord.ext import commands
import Constants.StringConstants as StringConstants
from Utils.NetworkUtils import NetworkUtils
from embeds.custom import VoiceEmbeds
from Voice import Off, Speak, Salute, Radio, YoutubeStream, SpotifyStream

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
        playing_state = self.client.voice.get_playing_state(ctx)
        if (not isinstance(playing_state, Speak) or not isinstance(playing_state, Salute)) and not await self._is_user_in_voice_channel(ctx):
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
        playing_state = self.client.voice.get_playing_state(ctx)
        if (not isinstance(playing_state, Speak) or not isinstance(playing_state, Salute)) and not await self._is_user_in_voice_channel(ctx):
            try:
                radios = self.client.bot_be.load_radios_config()
                selected_city = radios[city]
                selected_radio_url = selected_city["items"][int(radio_id) - 1]["link"]
                selected_radio_name = selected_city['items'][int(radio_id) - 1]['name']
                await self.client.voice.play_radio(selected_radio_url, ctx, selected_radio_name)
            except IndexError:
                await ctx.send("Escribe bien cojudo, usa `-radios`")
            

    async def _is_user_in_voice_channel(self, ctx):
        if not ctx.author.voice:
            await ctx.send(StringConstants.NOT_IN_VOICE_CHANNEL_MSG)
            return True
        return False

    @commands.command(aliases=["st", "vete-mierda", "stop"], name="stop-radio")
    async def stop(self, ctx):
        '''Para lo que sea que dice el bot y lo bota del canal
        '''
        playing_state = self.client.voice.get_playing_state(ctx)
        if not await self._is_user_in_voice_channel(ctx):
            await ctx.sad_reaction()
            await self.client.voice.disconnect_player(ctx)

    @commands.command(name="metele", aliases=["dale", "entrale", "reproduce", "hazme-la-taba"])
    async def play_for_stream(self, ctx, *query):
        '''Reproduce queries y links de Youtube asi como playlists de spotify.
        Ejemplo {command_prefix}metele https://open.spotify.com/playlist/37i9dQZEVXbLiRSasKsNU9
        O {command_prefix}metele https://www.youtube.com/watch?v=l00VTUYkebw
        O {command_prefix}metele chuchulun don omar
        '''
        if not query:
            return await ctx.message.add_reaction('❌')
        if "https://open.spotify.com" in str(query[0]) and "playlist" in str(query[0]):
            await self.handle_query_for_spotify(str(query[0]), ctx)
        elif "youtube.com" in str(query) or ".com" not in str(query):
            await self.handle_query_for_youtube(query, ctx)

    async def handle_query_for_youtube(self, query, ctx):
        playing_state = self.client.voice.get_playing_state(ctx)
        if (not isinstance(playing_state, Speak) or not isinstance(playing_state, Salute)) and not await self._is_user_in_voice_channel(ctx):
            await self.client.voice.play_for_youtube(query, ctx)
            embed_options = {'title': f'Agregando a lista de reproduccion con busqueda: {" ".join(query)}'}
            embed = VoiceEmbeds(author=ctx.author, **embed_options)
            await ctx.send(embed=embed, delete_after=8.0)

    async def handle_query_for_spotify(self, query, ctx):
        playing_state = self.client.voice.get_playing_state(ctx)
        if (not isinstance(playing_state, Speak) or not isinstance(playing_state, Salute)) and not await self._is_user_in_voice_channel(ctx):
            await self.client.voice.play_for_spotify(query, ctx)

    @commands.command(name="sig", aliases=["siguiente"])
    async def next_song_in_queue(self, ctx):
        '''Va a la siguiente cancion en la lista de canciones registradas con `-metele`
        '''
        playing_state = self.client.voice.get_playing_state(ctx)
        if not await self._is_user_in_voice_channel(ctx) and (isinstance(playing_state, YoutubeStream) or isinstance(playing_state, SpotifyStream)):
            self.client.voice.stop_player(ctx)

    @commands.command(name="pausa")
    async def pause(self, ctx):
        '''Pausea el bot
        '''
        if not await self._is_user_in_voice_channel(ctx):
            self.client.voice.pause_player(ctx)
            await ctx.message.add_reaction('⏸️')

    @commands.command(name="sigue")
    async def resume(self, ctx):
        '''Continua con la reproduccion
        '''
        if not await self._is_user_in_voice_channel(ctx):
            self.client.voice.resume_player(ctx)
            await ctx.message.add_reaction('▶️')

    @commands.command(aliases=["v"], name="volumen")
    async def set_voice_volume(self, ctx, volume: float):
        '''Setea el volumen a un %
        `-volumen [0-100]`'''
        if volume < 0 or volume > 100:
            return await ctx.send("No seas pendejo")
        playing_state = self.client.voice.get_playing_state(ctx)
        if not await self._is_user_in_voice_channel(ctx) and not isinstance(playing_state, Off):
            await ctx.send(f"Volumen seteado al {volume}%")
            self.client.voice.set_volume(volume, ctx)

def setup(client):
    client.add_cog(voice(client))
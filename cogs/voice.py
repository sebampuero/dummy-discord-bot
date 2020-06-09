import discord
import os.path
from discord.ext import commands
import Constants.StringConstants as StringConstants
from Utils.NetworkUtils import NetworkUtils
from embeds.custom import VoiceEmbeds
from Voice import Off, Speak, Salute, Radio, Stream, StreamingType
from BE.BotBE import BotBE
class voice(commands.Cog):
    '''Todo lo necesario para hacer que el bot hable y reproduzca musiquita
    '''
    def __init__(self, client):
        self.client = client
        self.bot_be = BotBE()

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
        if (not isinstance(playing_state, Speak) and not isinstance(playing_state, Salute)) and await self._is_user_in_voice_channel(ctx):
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
    @commands.cooldown(1.0, 5.0, commands.BucketType.guild)
    async def start_radio(self, ctx, city, radio_id):
        '''Inicia la radio con la ciudad y su radio correspondiente
        `-start-radio o -sr [ciudad] [numero de radio]`
        '''
        playing_state = self.client.voice.get_playing_state(ctx)
        if (not isinstance(playing_state, Speak) and not isinstance(playing_state, Salute)) and await self._is_user_in_voice_channel(ctx):
            try:
                radios = self.client.bot_be.load_radios_config()
                selected_city = radios[city.lower()]
                selected_radio_url = selected_city["items"][int(radio_id) - 1]["link"]
                selected_radio_name = selected_city['items'][int(radio_id) - 1]['name']
                await self.client.voice.play_radio(selected_radio_url, ctx, selected_radio_name)
                await ctx.processing_command_reaction()
            except IndexError:
                await ctx.send("Escribe bien cojudo, usa `-radios`")
            

    async def _is_user_in_voice_channel(self, ctx):
        if ctx.author.voice:
            return True
        await ctx.send(StringConstants.NOT_IN_VOICE_CHANNEL_MSG)
        return False

    @commands.command(aliases=["st", "vete-mierda", "stop"], name="stop-radio")
    async def stop(self, ctx):
        '''Para lo que sea que dice el bot y lo bota del canal
        '''
        playing_state = self.client.voice.get_playing_state(ctx)
        if await self._is_user_in_voice_channel(ctx):
            await ctx.sad_reaction()
            await self.client.voice.disconnect_player(ctx)

    @commands.command(name="metele", aliases=["dale", "entrale", "reproduce", "hazme-la-taba"])
    @commands.cooldown(1.0, 5.0, commands.BucketType.guild)
    async def play_for_stream(self, ctx, *query):
        '''Reproduce queries y links de Youtube asi como playlists de spotify.
        Ejemplo -metele https://open.spotify.com/playlist/37i9dQZEVXbLiRSasKsNU9
        O -metele https://www.youtube.com/watch?v=l00VTUYkebw
        O -metele chuchulun don omar
        '''
        playing_state = self.client.voice.get_playing_state(ctx)
        if not query:
            return await ctx.bad_command_reaction()
        playing_state = self.client.voice.get_playing_state(ctx)
        if (not isinstance(playing_state, Speak) and not isinstance(playing_state, Salute)) and await self._is_user_in_voice_channel(ctx):
            if "https://open.spotify.com" in str(query[0]) and "playlist" in str(query[0]):
                await self.client.voice.play_streaming(str(query[0]), StreamingType.SPOTIFY, ctx)
                await ctx.processing_command_reaction()
            elif "youtube.com" in str(query) or ".com" not in str(query):
                await self.client.voice.play_streaming(query, StreamingType.YOUTUBE,  ctx)
                await ctx.processing_command_reaction()
            else:
                await ctx.send(f"No tengo soporte aun para {str(query)}")

    @commands.command(name="sig", aliases=["siguiente"])
    @commands.cooldown(1.0, 5.0, commands.BucketType.guild)
    async def next_song_in_queue(self, ctx):
        '''Va a la siguiente cancion en la lista de canciones de Spotify o Youtube
        '''
        playing_state = self.client.voice.get_playing_state(ctx)
        if await self._is_user_in_voice_channel(ctx) and (isinstance(playing_state, Stream)):
            await self.client.voice.next_in_queue(ctx)
            await ctx.processing_command_reaction()

    @commands.command(name="pausa")
    async def pause(self, ctx):
        '''Pausea el bot
        '''
        if await self._is_user_in_voice_channel(ctx):
            self.client.voice.pause_player(ctx)
            await ctx.message.add_reaction('⏸️')

    @commands.command(name="sigue")
    async def resume(self, ctx):
        '''Continua con la reproduccion
        '''
        if await self._is_user_in_voice_channel(ctx):
            self.client.voice.resume_player(ctx)
            await ctx.message.add_reaction('▶️')

    @commands.command(aliases=["vol"], name="volumen")
    async def set_voice_volume(self, ctx, volume):
        '''Setea el volumen a un %
        `-volumen [0-100]`'''
        if volume < 0 or volume > 100:
            return await ctx.send("No seas pendejo")
        playing_state = self.client.voice.get_playing_state(ctx)
        if await self._is_user_in_voice_channel(ctx) and not isinstance(playing_state, Off):
            await ctx.send(f"Volumen seteado al {volume}%")
            self.client.voice.set_volume(volume, ctx)

    @commands.command(aliases=["sh"], name="shuffle")
    async def set_shuffle_for_queue(self, ctx):
        '''Activa o desactiva el shuffle de una lista de reproduccion
        '''
        playing_state = self.client.voice.get_playing_state(ctx)
        if await self._is_user_in_voice_channel(ctx) and (isinstance(playing_state, Stream)):
            is_shuffle = self.client.voice.trigger_shuffle(ctx)
            msg = "Shuffle activado" if is_shuffle else "Shuffle desactivado"
            await ctx.send(msg)

    @commands.command(name="loop")
    async def set_loop_for_song(self, ctx):
        '''Activa o desactiva el loop de una cancion en la lista de reproduccion
        '''
        playing_state = self.client.voice.get_playing_state(ctx)
        if await self._is_user_in_voice_channel(ctx) and (isinstance(playing_state, Stream)):
            is_loop = self.client.voice.trigger_loop_for_song(ctx)
            msg =  "Loop activado" if is_loop else "Loop desactivado"
            await ctx.send(msg)

    @commands.group(name="lista")
    async def queue(self, ctx):
        '''Functiones especificas sobre la lista de reproduccion
        '''
        if ctx.invoked_subcommand is None:
            await ctx.send('Especifica que quieres saber de la lista de reproduccion')

    @queue.command(name="t")
    async def queue_size(self, ctx):
        '''Revela el numero de canciones que hay en la lista de reproduccion
        '''
        playing_state = self.client.voice.get_playing_state(ctx)
        if isinstance(playing_state, Stream):
            return await ctx.send(f"Canciones en lista: {self.client.voice.get_stream_queue_size(ctx)}")
        else:
            return await ctx.send("No se esta reproduciendo ninguna lista")

    @queue.command(name="l")
    async def queue_songs_list(self, ctx, page):
        '''Muestra las busquedas y canciones que estan actualmente en la lista de reproduccion.
        Ejemplo `-lista l [numero de pagina]` 10 resultados por busqueda
        '''
        page = int(page)
        if page < 1:
            return await ctx.send("No seas huevon")
        results_per_page = 10
        start_idx = page * results_per_page - results_per_page
        end_idx = page * results_per_page - 1
        playing_state = self.client.voice.get_playing_state(ctx)
        if isinstance(playing_state, Stream):
            queue = self.client.voice.get_queue(ctx)
            if not queue or len(queue) == 0:
                return await ctx.send("No hay una lista de reproduccion")
            paginated_queue = queue[start_idx:end_idx+1]
            msg = ""
            for idx, entry in enumerate(paginated_queue):
                msg += f"`{start_idx + 1 + idx}` {entry}\n"
            return await ctx.send(msg) if msg != "" else await ctx.send(f"No hay resultados para pagina {page}")

    @commands.command(name="agregar-saludo", aliases=["saludo"])
    async def add_audio_for_user(self, ctx):
        '''Agrega un saludo
        `-saludo` o `-agregar-saludo [@miembro]`
        El audio insertado debe ser MP3 y no ser mas grande de 300KB
        '''
        if len(ctx.message.attachments) != 1:
            return await ctx.send("Debes subir 1 solo audio")
        if len(ctx.message.mentions) == 0 or len(ctx.message.mentions) > 1:
            return await ctx.send("Debes tagear a una sola persona")
        if not str(ctx.message.attachments[0].filename).endswith(".mp3"):
            return await ctx.send("Debe ser un archivo MP3")
        if ctx.message.attachments[0].size / 1000 > 300:
            return await ctx.send(f"El archivo puede ser maximo de 300KB. Peso: {ctx.message.attachments[0].size / 1000}KB")
        user_id = ctx.message.raw_mentions[0]
        user_id_filename_placeholder = user_id
        filename_to_save = f"./assets/audio/{user_id_filename_placeholder}.mp3"
        while os.path.isfile(filename_to_save):
            user_id_filename_placeholder += 1
            filename_to_save = f"./assets/audio/{user_id_filename_placeholder}.mp3"
        await ctx.message.attachments[0].save(filename_to_save)
        self.bot_be.save_audio_for_user(filename_to_save, user_id, ctx.guild.id)
        await ctx.send("Agregado papu")

def setup(client):
    client.add_cog(voice(client))
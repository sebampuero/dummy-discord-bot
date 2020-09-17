import discord
import os.path
from discord.ext import commands
import Constants.StringConstants as StringConstants
from Utils.NetworkUtils import NetworkUtils
from embeds.custom import VoiceEmbeds
from Functionalities.Voice.VoiceState import *
from Functionalities.Voice.Voice import StreamingType
from BE.BotBE import BotBE
from Utils.TTS import TTS
from Utils.TimeUtils import TimeUtils
from embeds.custom import GeneralEmbed
import logging
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

    async def execute_voice_handling(self, ctx, language, text):
        playing_state = self.client.voice.get_playing_state(ctx)
        if (not isinstance(playing_state, Speak) and not isinstance(playing_state, Salute)) and await self._is_user_in_voice_channel(ctx):
            try:
                url = TTS.get_tts_url(text, language)
                network_utils = NetworkUtils()
                status, content_type = await network_utils.website_check(url)
                if status == 200:
                    await self.client.voice.reproduce_from_file(ctx.author, url)
                else:
                    await ctx.send(StringConstants.SMTH_FUCKED_UP)
            except Exception as e:
                logging.error("while reproducing get_tts_url", exc_info=True)
                await ctx.send("El formato de idioma no existe")

    @commands.command(name="say")
    @commands.cooldown(1.0, 3.0, commands.BucketType.guild)
    async def say(self, ctx, *, text):
        '''Texto a voz en español
        '''
        try:
            lang_index_first = text.index("/")
            lang_index_sec = text.rindex("/")
            if lang_index_first == lang_index_sec:
                raise ValueError()
            language = text[lang_index_first+1:lang_index_sec]
            text = text.replace(f"/{language}/", "")
            await self.execute_voice_handling(ctx, language, text)
        except ValueError:
            await self.execute_voice_handling(ctx, "es-es", text)
        except Exception:
            await ctx.send("Si escribes el idioma, tiene que ser entre `//`")
        
    @commands.command(aliases=["radios"], name="show-radios")
    async def show_radios(self, ctx):
        '''Muestra todas las radios disponibles
        '''
        radios = self.client.bot_be.load_radios_msg()
        options = {
                'title': 'Radios disponibles',
                'fields': []
            }
        for key, value in radios.items():
            field = dict()
            field["name"] = str(key)
            field["value"] = ""
            for idx, radio in enumerate(value["items"]):
                field["value"] += f" `{idx+1}` " + radio["name"] + "\n"
            field["inline"] = True
            options["fields"].append(field)
        return await ctx.send(embed=GeneralEmbed.from_dict(options)) if bool(radios) else await ctx.send("No hay radios")

    @commands.command(aliases=["sr"], name="start-radio")
    @commands.cooldown(1.0, 3.0, commands.BucketType.guild)
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
                await ctx.send("Esa radio no existe, usa `-radios`")
            
    
    @commands.command(name="save-radio", aliases=["svr"])
    async def save_radio(self, ctx, url, city_key, city_big, name):
        """Agregar una radio a la lista de radios
        `-save-radio o -svr [url] [palabra clave de ciudad] [ciudad] [nombre de la radio]`
        """
        network_utils = NetworkUtils()
        status, content_type = await network_utils.website_check(str(url))
        if status == 200 and (content_type == "audio/mpeg" or content_type == "audio/aacp" or content_type == "audio/aac"):
            self.client.bot_be.save_radios(url, city_key, city_big, name)
            await ctx.good_command_reaction()
        else:
            await ctx.send("No es el link de una radio valida")
            
    async def _is_user_in_voice_channel(self, ctx):
        if ctx.author.voice:
            return True
        await ctx.send(StringConstants.NOT_IN_VOICE_CHANNEL_MSG)
        return False

    @commands.command(aliases=["st","stop"], name="stop-radio")
    async def stop(self, ctx):
        '''Para lo que sea que dice el bot y lo bota del canal
        '''
        if await self._is_user_in_voice_channel(ctx):
            await ctx.sad_reaction()
            await self.client.voice.disconnect_player(ctx)

    @commands.command(name="seek", aliases=["sk"])
    @commands.cooldown(1.0, 3.0, commands.BucketType.guild)
    async def seek(self, ctx, second):
        '''Avanza el stream hasta el segundo determinado
        Ejemplo: `-seek 50`
        '''
        playing_state = self.client.voice.get_playing_state(ctx)
        if isinstance(playing_state, Stream):
            try:
                second = int(second)
                self.client.voice.seek(ctx, second)
                await ctx.processing_command_reaction()
            except Exception as e:
                logging.warning(str(e), exc_info=True)
                await ctx.send("No pes")

    @commands.command(name="rewind", aliases=["rwd"])
    @commands.cooldown(1.0, 3.0, commands.BucketType.guild)
    async def rewind(self, ctx):
        '''Rewind de 10 segundos en la cancion actual
        '''
        playing_state = self.client.voice.get_playing_state(ctx)
        if isinstance(playing_state, Stream):
            current_second = self.client.voice.get_song_timestamp_progress(ctx)
            await self.seek(ctx, current_second - 10)
            await ctx.processing_command_reaction()

    @commands.command(name="timestamp", aliases=["ts"])
    @commands.cooldown(1.0, 3.0, commands.BucketType.guild)
    async def song_progress(self, ctx):
        '''Muestra por que hora, minuto y segundo esta la cancion actual'''
        playing_state = self.client.voice.get_playing_state(ctx)
        if isinstance(playing_state, Stream):
            current_second = self.client.voice.get_song_timestamp_progress(ctx)
            await ctx.send(TimeUtils.parse_seconds(current_second))

    @commands.command(name="fast-forward", aliases=["fwd"])
    @commands.cooldown(1.0, 3.0, commands.BucketType.guild)
    async def fast_forward(self, ctx):
        '''Fast forward de 10 segundos en la cancion actual'''
        playing_state = self.client.voice.get_playing_state(ctx)
        if isinstance(playing_state, Stream):
            current_second = self.client.voice.get_song_timestamp_progress(ctx)
            await self.seek(ctx, current_second + 10)
            await ctx.processing_command_reaction()

    @commands.command(name="metele", aliases=["go", "pl"])
    @commands.cooldown(1.0, 3.0, commands.BucketType.guild)
    async def play_for_stream(self, ctx, *query):
        '''Reproduce queries y links de Youtube asi como playlists de spotify y soundcloud.
        Ejemplo -metele https://open.spotify.com/playlist/37i9dQZEVXbLiRSasKsNU9
        -metele https://soundcloud.com/djasto-1/dj-asto-ft-dj-deeper-flamingo-mix
        O -metele https://www.youtube.com/watch?v=l00VTUYkebw
        O -metele chuchulun don omar
        '''
        playing_state = self.client.voice.get_playing_state(ctx)
        if (not isinstance(playing_state, Speak) and not isinstance(playing_state, Salute)) and await self._is_user_in_voice_channel(ctx):
            if not query:
                if len(ctx.message.attachments) == 1:
                    if str(ctx.message.attachments[0].filename).endswith(".mp3"):
                        await self.client.voice.play_streaming(ctx.message.attachments[0], StreamingType.MP3_FILE, ctx)
                        await ctx.processing_command_reaction()
                else:
                    await ctx.send("Adjunta un archivo mp3 si no escribes nada")
            elif "https://open.spotify.com" in str(query[0]) and "playlist" in str(query[0]):
                await self.client.voice.play_streaming(str(query[0]), StreamingType.SPOTIFY, ctx)
                await ctx.processing_command_reaction()
            elif "youtube.com" in str(query) or ".com" not in str(query):
                await self.client.voice.play_streaming(query, StreamingType.YOUTUBE,  ctx)
                await ctx.processing_command_reaction()
            elif "https://soundcloud.com" in str(query[0]):
                await self.client.voice.play_streaming(str(query[0]), StreamingType.SOUNDCLOUD, ctx)
                await ctx.processing_command_reaction()
            else:
                await ctx.send(f"No tengo soporte aun para {str(query)}")

    @commands.command(name="sig", aliases=["next", "s"])
    @commands.cooldown(1.0, 3.0, commands.BucketType.guild)
    async def next_song_in_queue(self, ctx):
        '''Va a la siguiente cancion en la lista de canciones
        '''
        playing_state = self.client.voice.get_playing_state(ctx)
        if await self._is_user_in_voice_channel(ctx) and (isinstance(playing_state, Stream)):
            await self.client.voice.next_in_queue(ctx)
            await ctx.processing_command_reaction()

    @commands.command(name="pause")
    async def pause(self, ctx):
        '''Pausea el bot
        '''
        if await self._is_user_in_voice_channel(ctx):
            self.client.voice.pause_player(ctx)
            await ctx.message.add_reaction('⏸️')

    @commands.command(name="continue")
    async def resume(self, ctx):
        '''Continua con la reproduccion
        '''
        if await self._is_user_in_voice_channel(ctx):
            self.client.voice.resume_player(ctx)
            await ctx.message.add_reaction('▶️')

    @commands.command(aliases=["vol"], name="volume")
    async def set_voice_volume(self, ctx, volume):
        '''Setea el volumen a un %
        `-volume [0-100]`'''
        volume = float(volume)
        if volume < 0 or volume > 100:
            return await ctx.send("No seas pendejo")
        playing_state = self.client.voice.get_playing_state(ctx)
        if await self._is_user_in_voice_channel(ctx) and not isinstance(playing_state, Off):
            await ctx.send(f"Volumen seteado al {volume}%")
            self.client.voice.set_volume(volume, ctx)

    @commands.command(aliases=["sh"], name="shuffle")
    async def set_shuffle_for_queue(self, ctx):
        '''Le mete su shuffle a la lista de reproduccion
        '''
        playing_state = self.client.voice.get_playing_state(ctx)
        if await self._is_user_in_voice_channel(ctx) and (isinstance(playing_state, Stream)):
            self.client.voice.trigger_shuffle(ctx)
            await ctx.send("Metiendole su shuffle csm!!")

    @commands.command(name="loop")
    async def set_loop_for_song(self, ctx):
        '''Activa o desactiva el loop de una cancion en la lista de reproduccion
        '''
        playing_state = self.client.voice.get_playing_state(ctx)
        if await self._is_user_in_voice_channel(ctx) and (isinstance(playing_state, Stream)):
            is_loop = self.client.voice.trigger_loop_for_song(ctx)
            msg =  "Loop activado" if is_loop else "Loop desactivado"
            await ctx.send(msg)

    @commands.group(name="list")
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

    @queue.command(name="p")
    async def queue_play(self, ctx, song_number):
        '''Reproduce una cancion de la lista con el numero asignado
        '''
        playing_state = self.client.voice.get_playing_state(ctx)
        if isinstance(playing_state, Stream):
            try:
                song_number = int(song_number)
                queue = self.client.voice.get_queue(ctx)
                searched_song = queue[song_number - 1]
                queue.append(searched_song)
                queue.pop(song_number - 1)
                await self.next_song_in_queue(ctx)
            except (IndexError, ValueError):
                await ctx.send("Ese numero de cancion no existe")

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
            options = {
                'title': 'Canciones en lista',
                'fields': []
            }
            for idx, entry in enumerate(paginated_queue):
                field = dict()
                field["name"] = str(entry)
                field["value"] = f"Numero: `{start_idx + 1 + idx}`"
                field["inline"] = True
                options["fields"].append(field)
            return await ctx.send(embed=GeneralEmbed.from_dict(options)) if len(paginated_queue) != 0 else await ctx.send(f"No hay resultados para pagina {page}")

    @commands.group(name="playl")
    async def playlist(self, ctx):
        '''Comandos para guardar y ver playlists guardadas
        '''
        if ctx.invoked_subcommand is None:
            await ctx.send('Especifica una accion')

    @playlist.command(name="save")
    async def playlist_save(self, ctx, url, name):
        '''Guarda una url de playlist
        '''
        url = str(url)
        name = str(name)
        if "https://open.spotify.com" in url and "playlist" in url:
            ack = self.client.bot_be.save_playlist_for_user(str(ctx.author.id), url, name)
            await ctx.send(ack)
        else:
            await ctx.send("No es una playlist de spotify")

    @playlist.command(name="read")
    async def playlist_read(self, ctx):
        '''Muestra las playlists guardadas
        '''
        playlists_list = self.client.bot_be.read_user_playlists(str(ctx.author.id))
        options = {
            "title": f"Playlists de {ctx.author.name}\n",
            "fields" : []
        }
        for idx, playlist_dict in enumerate(playlists_list):
            field = dict()
            field["name"] = playlist_dict['name']
            field["value"] = f"Numero: `{idx+1}`"
            field["inline"] = True
            options["fields"].append(field)
        await ctx.send(embed=GeneralEmbed.from_dict(options)) if len(playlists_list) != 0 else await ctx.send("Aun no has guardado playlists de spotify, usa `-playlist save [url] [nombre de playlist]`")

    @playlist.command(name="play")
    @commands.cooldown(1.0, 3.0, commands.BucketType.guild)
    async def playlist_playback(self, ctx, playlist):
        '''Reproduce una lista seleccionada
        '''
        try:
            playlist_id = int(playlist)
            await self._search_playlist(playlist_id, ctx)
        except ValueError:
            playlist_id = str(playlist)
            await self._search_playlist(playlist_id, ctx)

    @playlist.command(name="del")
    @commands.cooldown(1.0, 3.0, commands.BucketType.guild)
    async def playlist_delete(self, ctx, playlist):
        '''Elimina una playlist
        '''
        return_msg = self.client.bot_be.delete_playlist_for_user(str(ctx.author.id), playlist)
        await ctx.send(return_msg)

    @commands.group(name="fav")
    async def fav(self, ctx):
        '''Comandos para guardar canciones favoritas
        '''
        if ctx.invoked_subcommand is None:
            await ctx.send('Especifica una accion pues weberto, usa `-help fav`')

    @fav.command(name="save", aliases=["s"])
    @commands.cooldown(1.0, 3.0, commands.BucketType.guild)
    async def fav_save(self, ctx):
        '''Guarda la cancion actual reproduciendose en favoritos
        '''
        playing_state = self.client.voice.get_playing_state(ctx)
        if isinstance(playing_state, Stream):
            current_query = playing_state.last_query
            if isinstance(current_query, SoundcloudQuery):
                query_type = StreamingType.SOUNDCLOUD
            else:
                query_type = StreamingType.YOUTUBE
            result_msg = self.client.bot_be.save_fav_song(str(ctx.author.id), current_query, query_type)
            await ctx.send(result_msg)
        else:
            return await ctx.send("No hay ninguna cancion reproduciendose actualmente")

    @fav.command(name="play", aliases=["p"])
    @commands.cooldown(1.0, 3.0, commands.BucketType.guild)
    async def fav_play(self, ctx):
        '''Mete en lista de reproduccion las canciones de favoritos
        '''
        if await self._is_user_in_voice_channel(ctx):
            favs_dict = self.client.bot_be.get_favs(str(ctx.author.id))
            if len(favs_dict) == 0:
                return await ctx.send("No hay favoritos guardados")
            song_queries_dicts = [{'query': item['song'], 'type': item['query_type']} for item in favs_dict]
            await self.client.voice.play_streaming(song_queries_dicts, StreamingType.BULK_FAVS, ctx)

    @fav.command(name="del", aliases=["d"])
    @commands.cooldown(1.0, 3.0, commands.BucketType.guild)
    async def fav_delete(self, ctx, song_id):
        '''Borra cancion favorita segun su identificador
        '''
        try:
            self.client.bot_be.delete_fav(str(song_id), str(ctx.author.id))
            await ctx.send("Eliminada")
        except:
            await ctx.send("Hubo un error")

    @fav.command(name="show", aliases=["sh"])
    @commands.cooldown(1.0, 3.0, commands.BucketType.guild)
    async def fav_show(self, ctx):
        '''Muestra todas las canciones favoritas guardadas
        '''
        favs_dicts = self.client.bot_be.get_favs(str(ctx.author.id))
        options = {
            "title": f"Favoritos de {ctx.author.name}\n",
            "fields" : []
        }
        for idx, favs_dict in enumerate(favs_dicts):
            field = dict()
            field["name"] = favs_dict['song']
            field["value"] = f"Identificador: {favs_dict['song_id']}"
            field["inline"] = True
            options["fields"].append(field)
        await ctx.send(embed=GeneralEmbed.from_dict(options)) if len(favs_dicts) != 0 else await ctx.send("Aun no has guardado favoritos, usa `-help fav save`")

    async def _search_playlist(self, playlist_id, ctx):
        try:
            playlists_list = self.client.bot_be.read_user_playlists(str(ctx.author.id))
            playlist_url = ""
            if isinstance(playlist_id, int):
                playlist_url = playlists_list[playlist_id - 1]['url']
            elif isinstance(playlist_id, str):
                for a_dict in playlists_list:
                    if a_dict["name"] == playlist_id:
                        playlist_url = a_dict["url"]
                        break
                if playlist_url == "":
                    raise KeyError("List name not found in list")
            await self.play_for_stream(ctx, playlist_url)
        except KeyError:
            await ctx.send("No tienes una playlist guardada con ese numero o nombre, para guardar listas usa `-playl save`")

    @commands.command(name="add-audio", aliases=["audio"])
    async def add_audio_for_user(self, ctx):
        '''Agrega un saludo
        `-audio [@miembro]`
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
        self.client.bot_be.save_audio_for_user(filename_to_save, user_id, ctx.guild.id)
        await ctx.send("Agregado papu")

def setup(client):
    client.add_cog(voice(client))
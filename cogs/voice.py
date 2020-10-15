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
from exceptions.CustomException import NotValidSongTimestamp
from checks.Checks import *
import logging
class voice(commands.Cog):
    '''Everything you need to make the bot talk and play music
    '''
    def __init__(self, client):
        self.client = client

    @commands.command(aliases=["off"], name="audio-off")
    async def audio_off(self, ctx):
        '''Turn off your personal greeting
        '''
        await self.client.voice.deactivate_welcome_audio(ctx)

    @commands.command(aliases=["on"], name="audio-on")
    async def audio_on(self, ctx):
        '''Activate your personal greeting
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
                await ctx.send("Language format does not exist")

    @commands.command(name="say")
    @commands.cooldown(1.0, 3.0, commands.BucketType.guild)
    async def say(self, ctx, *, text):
        '''Text to speech in Spanish
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
            await ctx.send("If you write the language, it has to be between `//`")
        
    @commands.command(aliases=["radios"], name="show-radios")
    async def show_radios(self, ctx):
        '''Show all available radios
        '''
        radios = self.client.bot_be.load_radios_msg()
        options = {
                'title': 'Available radios',
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
        return await ctx.send(embed=GeneralEmbed.from_dict(options)) if bool(radios) else await ctx.send("No radios")

    @commands.command(aliases=["sr"], name="start-radio")
    @commands.cooldown(1.0, 3.0, commands.BucketType.guild)
    async def start_radio(self, ctx, city, radio_id):
        '''Start the radio with the city and its corresponding radio
         `-start-radio or -sr [city] [radio number]`
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
                await ctx.send("That radio does not exist, use `-radios`")
            
    
    @commands.command(name="save-radio", aliases=["svr"])
    async def save_radio(self, ctx, url, city_key, city_big, name):
        """Add a radio to the list of radios
         `-save-radio or -svr [url] [city keyword] [city] [radio name]`
        """
        network_utils = NetworkUtils()
        status, content_type = await network_utils.website_check(str(url))
        if status == 200 and (content_type == "audio/mpeg" or content_type == "audio/aacp" or content_type == "audio/aac"):
            self.client.bot_be.save_radios(url, city_key, city_big, name)
            await ctx.good_command_reaction()
        else:
            await ctx.send("Not a valid radio link")
            
    async def _is_user_in_voice_channel(self, ctx):
        if ctx.author.voice:
            return True
        await ctx.send(StringConstants.NOT_IN_VOICE_CHANNEL_MSG)
        return False

    @commands.command(aliases=["st","stop"], name="stop-radio")
    async def stop(self, ctx):
        '''Stops the music and leaves the voice channel
        '''
        if await self._is_user_in_voice_channel(ctx):
            await self.client.voice.shutdown_player(ctx)

    @commands.command(name="seek", aliases=["sk"])
    @commands.cooldown(1.0, 3.0, commands.BucketType.guild)
    async def seek(self, ctx, timestamp):
        '''Advance the stream to the specified second
         Example: `-seek 70` (70 seconds) or` -seek 1m:20s` (1 minute 20 seconds)
         o `-seek 1h:10m:10s` (1 hour 10 minutes 10 seconds)
        '''
        playing_state = self.client.voice.get_playing_state(ctx)
        if isinstance(playing_state, Stream):
            try:
                second = int(timestamp)
                await self.client.voice.seek(ctx, second)
                await ctx.processing_command_reaction()
            except ValueError: # incase it has the readable format
                try:
                    seconds = TimeUtils.parse_readable_format(timestamp)
                    await self.client.voice.seek(ctx, seconds)
                    await ctx.processing_command_reaction()
                except NotValidSongTimestamp:
                    await ctx.send("Invalid format, use something like `10m:50s o 1h:20m:20s o 20s`")
            except Exception as e:
                logging.warning(str(e), exc_info=True)
                await ctx.send("No pes")

    @commands.command(name="rewind", aliases=["rwd"])
    @commands.cooldown(1.0, 3.0, commands.BucketType.guild)
    async def rewind(self, ctx):
        '''10 seconds rewind on current song
        '''
        playing_state = self.client.voice.get_playing_state(ctx)
        if isinstance(playing_state, Stream):
            current_second = self.client.voice.get_song_timestamp_progress(ctx)
            await self.seek(ctx, current_second - 10)
            await ctx.processing_command_reaction()

    @commands.command(name="timestamp", aliases=["ts"])
    @commands.cooldown(1.0, 3.0, commands.BucketType.guild)
    async def song_progress(self, ctx):
        '''Shows what hour, minute and second the current song is playing in'''
        playing_state = self.client.voice.get_playing_state(ctx)
        if isinstance(playing_state, Stream):
            current_second = self.client.voice.get_song_timestamp_progress(ctx)
            await ctx.send(f"{TimeUtils.parse_seconds(current_second)} currently")

    @commands.command(name="fast-forward", aliases=["fwd"])
    @commands.cooldown(1.0, 3.0, commands.BucketType.guild)
    async def fast_forward(self, ctx):
        '''10 seconds fast forward on current song'''
        playing_state = self.client.voice.get_playing_state(ctx)
        if isinstance(playing_state, Stream):
            current_second = self.client.voice.get_song_timestamp_progress(ctx)
            await self.seek(ctx, current_second + 10)
            await ctx.processing_command_reaction()

    @commands.command(name="speed-up", aliases=["su"])
    @commands.cooldown(1.0, 3.0, commands.BucketType.guild)
    async def speed_up(self, ctx):
        '''Speeds up current song 2X
        '''
        playing_state = self.client.voice.get_playing_state(ctx)
        if isinstance(playing_state, Stream):
            await self.client.voice.apply_effect(ctx, Stream.Effect.SPEED_UP)
            await ctx.processing_command_reaction()

    @commands.command(name="slow-down", aliases=["sd"])
    @commands.cooldown(1.0, 3.0, commands.BucketType.guild)
    async def slow_down(self, ctx):
        '''Slows down current song 0.5X
        '''
        playing_state = self.client.voice.get_playing_state(ctx)
        if isinstance(playing_state, Stream):
            await self.client.voice.apply_effect(ctx, Stream.Effect.SLOW_DOWN)
            await ctx.processing_command_reaction()

    @commands.command(name="restore-effects", aliases=["re"])
    @commands.cooldown(1.0, 3.0, commands.BucketType.guild)
    async def restore_effects(self, ctx):
        '''Remove all effects and return the song to normal
        '''
        playing_state = self.client.voice.get_playing_state(ctx)
        if isinstance(playing_state, Stream):
            await self.client.voice.restore_stream(ctx)
            await ctx.processing_command_reaction()

    @commands.command(name="indoor-equalizer")
    @commands.cooldown(1.0, 3.0, commands.BucketType.guild)
    async def indoor_equalizer(self, ctx):
        '''Apply the indoor-equalizer effect on the current song
        '''
        playing_state = self.client.voice.get_playing_state(ctx)
        if isinstance(playing_state, Stream):
            await self.client.voice.apply_effect(ctx, Stream.Effect.EQUALIZER)
            await ctx.processing_command_reaction()

    @commands.command(name="weird")
    @commands.cooldown(1.0, 3.0, commands.BucketType.guild)
    async def weird(self, ctx):
        '''Apply the weird effect on the current song
        '''
        playing_state = self.client.voice.get_playing_state(ctx)
        if isinstance(playing_state, Stream):
            await self.client.voice.apply_effect(ctx, Stream.Effect.VAPORWAVE)
            await ctx.processing_command_reaction()

    @commands.command(name="bass")
    @commands.cooldown(1.0, 3.0, commands.BucketType.guild)
    async def bass(self, ctx):
        '''Apply the bass effect to the current song
        '''
        playing_state = self.client.voice.get_playing_state(ctx)
        if isinstance(playing_state, Stream):
            await self.client.voice.apply_effect(ctx, Stream.Effect.BASS)
            await ctx.processing_command_reaction()

    @commands.command(name="chorus")
    @commands.cooldown(1.0, 3.0, commands.BucketType.guild)
    async def chorus(self, ctx):
        '''Apply the chorus effect to the current song
        '''
        playing_state = self.client.voice.get_playing_state(ctx)
        if isinstance(playing_state, Stream):
            await self.client.voice.apply_effect(ctx, Stream.Effect.CHORUS)
            await ctx.processing_command_reaction()

    @commands.command(name="ear-rape")
    @commands.cooldown(1.0, 3.0, commands.BucketType.guild)
    async def ear_rape(self, ctx):
        '''Apply the ear rape effect to the current song
        '''
        playing_state = self.client.voice.get_playing_state(ctx)
        if isinstance(playing_state, Stream):
            await self.client.voice.apply_effect(ctx, Stream.Effect.EAR_RAPE)
            await ctx.processing_command_reaction()

    @commands.command(name="eight-sim")
    @commands.cooldown(1.0, 3.0, commands.BucketType.guild)
    async def eight_sim(self, ctx):
        '''Apply the 8M Sim effect to the current song
        '''
        playing_state = self.client.voice.get_playing_state(ctx)
        if isinstance(playing_state, Stream):
            await self.client.voice.apply_effect(ctx, Stream.Effect.EIGHTM_SIM)
            await ctx.processing_command_reaction()

    @commands.command(name="vaporwave")
    @commands.cooldown(1.0, 3.0, commands.BucketType.guild)
    async def vaporwave(self, ctx):
        '''Apply the vaporwave effect on the current song
        '''
        playing_state = self.client.voice.get_playing_state(ctx)
        if isinstance(playing_state, Stream):
            await self.client.voice.apply_effect(ctx, Stream.Effect.VIBRATO)
            await ctx.processing_command_reaction()

    @commands.command(name="metal")
    @commands.cooldown(1.0, 3.0, commands.BucketType.guild)
    async def metal(self, ctx):
        '''Apply the metal effect to the current song
        '''
        playing_state = self.client.voice.get_playing_state(ctx)
        if isinstance(playing_state, Stream):
            await self.client.voice.apply_effect(ctx, Stream.Effect.METAL)
            await ctx.processing_command_reaction()

    @commands.command(name="super-eq")
    @commands.cooldown(1.0, 3.0, commands.BucketType.guild)
    async def super_equalizer(self, ctx):
        '''Apply the super equalizer effect on the current song
        '''
        playing_state = self.client.voice.get_playing_state(ctx)
        if isinstance(playing_state, Stream):
            await self.client.voice.apply_effect(ctx, Stream.Effect.SUPEREQUALIZER)
            await ctx.processing_command_reaction()

    @commands.command(name="test-effect")
    @is_owner()
    async def test_filter(self, ctx, ffmpeg_filter):
        '''Filter test for ffmpeg. Authorized use only.
        '''
        playing_state = self.client.voice.get_playing_state(ctx)
        if isinstance(playing_state, Stream):
            await self.client.voice.test_filter(ctx, ffmpeg_filter)

    @commands.command(name="go", aliases=["pl", "metele"])
    @commands.cooldown(1.0, 3.0, commands.BucketType.guild)
    async def play_for_stream(self, ctx, *query):
        '''Play queries and YouTube links as well as spotify and soundcloud playlists.
         Example -go https://open.spotify.com/playlist/37i9dQZEVXbLiRSasKsNU9
         -go https://soundcloud.com/djasto-1/dj-asto-ft-dj-deeper-flamingo-mix
         O -go https://www.youtube.com/watch?v=l00VTUYkebw
         O -go chuchulun don omar
        '''
        playing_state = self.client.voice.get_playing_state(ctx)
        if (not isinstance(playing_state, Speak) and not isinstance(playing_state, Salute)) and await self._is_user_in_voice_channel(ctx):
            if not query:
                if len(ctx.message.attachments) == 1:
                    if str(ctx.message.attachments[0].filename).endswith(".mp3"):
                        await self.client.voice.play_streaming(ctx.message.attachments[0], StreamingType.MP3_FILE, ctx)
                        await ctx.processing_command_reaction()
                else:
                    await ctx.send("Attach an mp3 file if you don't write anything")
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
        '''Goes to the next song in the song list
        '''
        playing_state = self.client.voice.get_playing_state(ctx)
        if await self._is_user_in_voice_channel(ctx) and (isinstance(playing_state, Stream)):
            await self.client.voice.next_in_queue(ctx)
            await ctx.processing_command_reaction()

    @commands.command(name="pause")
    async def pause(self, ctx):
        '''Pause
        '''
        if await self._is_user_in_voice_channel(ctx):
            self.client.voice.pause_player(ctx)
            await ctx.message.add_reaction('⏸️')

    @commands.command(name="continue")
    async def resume(self, ctx):
        '''Continues
        '''
        if await self._is_user_in_voice_channel(ctx):
            self.client.voice.resume_player(ctx)
            await ctx.message.add_reaction('▶️')

    @commands.command(aliases=["vol"], name="volume")
    async def set_voice_volume(self, ctx, volume):
        '''Sets volume
        `-volume [0-100]`'''
        volume = float(volume)
        if volume < 0 or volume > 100:
            return await ctx.send("No seas pendejo")
        playing_state = self.client.voice.get_playing_state(ctx)
        if await self._is_user_in_voice_channel(ctx) and not isinstance(playing_state, Off):
            self.client.voice.set_volume(volume, ctx)

    @commands.command(aliases=["sh"], name="shuffle")
    async def set_shuffle_for_queue(self, ctx):
        '''Shuffle the list
        '''
        playing_state = self.client.voice.get_playing_state(ctx)
        if await self._is_user_in_voice_channel(ctx) and (isinstance(playing_state, Stream)):
            self.client.voice.trigger_shuffle(ctx)
            await ctx.send("Metiendole su shuffle csm!!")

    @commands.command(name="loop")
    async def set_loop_for_song(self, ctx):
        '''Enables or disables the loop of a song in the playlist
        '''
        playing_state = self.client.voice.get_playing_state(ctx)
        if await self._is_user_in_voice_channel(ctx) and (isinstance(playing_state, Stream)):
            is_loop = self.client.voice.trigger_loop_for_song(ctx)
            msg =  "Loop on" if is_loop else "Loop off"
            await ctx.send(msg)

    @commands.group(name="list")
    async def queue(self, ctx):
        '''Specific functions on the playlist
        '''
        if ctx.invoked_subcommand is None:
            await ctx.send('Specify what you want to know about the playlist')

    @queue.command(name="t")
    async def queue_size(self, ctx):
        '''Reveal the number of songs in the playlist
        '''
        playing_state = self.client.voice.get_playing_state(ctx)
        if isinstance(playing_state, Stream):
            return await ctx.send(f"Songs in the list: {self.client.voice.get_stream_queue_size(ctx)}")
        else:
            return await ctx.send("No playlist is playing")

    @queue.command(name="p")
    async def queue_play(self, ctx, song_number):
        '''Play a song from the list with the assigned number
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
                await ctx.send("That song number does not exist")

    @queue.command(name="l")
    async def queue_songs_list(self, ctx, page):
        '''Shows the queries and songs that are currently in the playlist.
            Example `-list l [page number]` 10 results per search
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
                return await ctx.send("There is no playlist")
            paginated_queue = queue[start_idx:end_idx+1]
            options = {
                'title': 'Songs',
                'fields': []
            }
            for idx, entry in enumerate(paginated_queue):
                field = dict()
                field["name"] = str(entry)
                field["value"] = f"Number: `{start_idx + 1 + idx}`"
                field["inline"] = True
                options["fields"].append(field)
            return await ctx.send(embed=GeneralEmbed.from_dict(options)) if len(paginated_queue) != 0 else await ctx.send(f"No results for page {page}")

    @commands.group(name="playl")
    async def playlist(self, ctx):
        '''Commands for saving and viewing saved playlists
        '''
        if ctx.invoked_subcommand is None:
            await ctx.send('Specify an action')

    @playlist.command(name="save")
    async def playlist_save(self, ctx, url, name):
        '''Save a playlist url
        '''
        url = str(url)
        name = str(name)
        if "https://open.spotify.com" in url and "playlist" in url:
            ack = self.client.bot_be.save_playlist_for_user(str(ctx.author.id), url, name)
            await ctx.send(ack)
        else:
            await ctx.send("Not a spotify playlist")

    @playlist.command(name="read")
    async def playlist_read(self, ctx):
        '''Show saved playlists
        '''
        playlists_list = self.client.bot_be.read_user_playlists(str(ctx.author.id))
        options = {
            "title": f"{ctx.author.name}'s playlists\n",
            "fields" : []
        }
        for idx, playlist_dict in enumerate(playlists_list):
            field = dict()
            field["name"] = playlist_dict['name']
            field["value"] = f"Number: `{idx+1}`"
            field["inline"] = True
            options["fields"].append(field)
        await ctx.send(embed=GeneralEmbed.from_dict(options)) if len(playlists_list) != 0 else await ctx.send("You haven't saved spotify playlists yet, use `-playlist save [url] [playlist name]`")

    @playlist.command(name="play")
    @commands.cooldown(1.0, 3.0, commands.BucketType.guild)
    async def playlist_playback(self, ctx, playlist):
        '''Play a selected list
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
        '''Delete a playlist
        '''
        return_msg = self.client.bot_be.delete_playlist_for_user(str(ctx.author.id), playlist)
        await ctx.send(return_msg)

    @commands.group(name="fav")
    async def fav(self, ctx):
        '''Commands for saving favorite songs
        '''
        if ctx.invoked_subcommand is None:
            await ctx.send('Specify an action pues weberto, use `-help fav`')

    @fav.command(name="save", aliases=["s"])
    @commands.cooldown(1.0, 3.0, commands.BucketType.guild)
    async def fav_save(self, ctx):
        '''Save the current song playing in favorites
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
            return await ctx.send("There is no song currently playing")

    @fav.command(name="play", aliases=["p"])
    @commands.cooldown(1.0, 3.0, commands.BucketType.guild)
    async def fav_play(self, ctx):
        '''Put favorites songs in playlist
        '''
        if await self._is_user_in_voice_channel(ctx):
            favs_dict = self.client.bot_be.get_favs(str(ctx.author.id))
            if len(favs_dict) == 0:
                return await ctx.send("No saved favorites")
            song_queries_dicts = [{'query': item['song'], 'type': item['query_type']} for item in favs_dict]
            await self.client.voice.play_streaming(song_queries_dicts, StreamingType.BULK_FAVS, ctx)

    @fav.command(name="del", aliases=["d"])
    @commands.cooldown(1.0, 3.0, commands.BucketType.guild)
    async def fav_delete(self, ctx, song_id):
        '''Delete favorite song according to your identifier
        '''
        try:
            self.client.bot_be.delete_fav(str(song_id), str(ctx.author.id))
            await ctx.send("Deleted")
        except:
            await ctx.send("There was an error")

    @fav.command(name="show", aliases=["sh"])
    @commands.cooldown(1.0, 3.0, commands.BucketType.guild)
    async def fav_show(self, ctx):
        '''Show all saved favorite songs
        '''
        favs_dicts = self.client.bot_be.get_favs(str(ctx.author.id))
        options = {
            "title": f"{ctx.author.name}'s favorites\n",
            "fields" : []
        }
        for idx, favs_dict in enumerate(favs_dicts):
            field = dict()
            field["name"] = favs_dict['song']
            field["value"] = f"ID: {favs_dict['song_id']}"
            field["inline"] = True
            options["fields"].append(field)
        await ctx.send(embed=GeneralEmbed.from_dict(options)) if len(favs_dicts) != 0 else await ctx.send("You haven't saved any favorites yet, use `-help fav save`")

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
            await ctx.send("You don't have a playlist saved with that number or name, to save playlists use `-playl save`")

    @commands.command(name="add-audio", aliases=["audio"])
    async def add_audio_for_user(self, ctx):
        '''Add a greeting
         `-audio [@member]`
         The inserted audio must be MP3 and not be larger than 300KB
        '''
        if len(ctx.message.attachments) != 1:
            return await ctx.send("Only 1 audio file")
        if len(ctx.message.mentions) == 0 or len(ctx.message.mentions) > 1:
            return await ctx.send("Tag someone")
        if not str(ctx.message.attachments[0].filename).endswith(".mp3"):
            return await ctx.send("Must be a MP3 file")
        if ctx.message.attachments[0].size / 1000 > 300:
            return await ctx.send(f"File size must not exceed 300KB. Size: {ctx.message.attachments[0].size / 1000}KB")
        user_id = ctx.message.raw_mentions[0]
        user_id_filename_placeholder = user_id
        filename_to_save = f"./assets/audio/{user_id_filename_placeholder}.mp3"
        while os.path.isfile(filename_to_save):
            user_id_filename_placeholder += 1
            filename_to_save = f"./assets/audio/{user_id_filename_placeholder}.mp3"
        await ctx.message.attachments[0].save(filename_to_save)
        self.client.bot_be.save_audio_for_user(filename_to_save, user_id, ctx.guild.id)
        await ctx.send("Added papu")

def setup(client):
    client.add_cog(voice(client))
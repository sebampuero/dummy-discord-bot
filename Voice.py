import asyncio
import discord
import random
import logging
import spotipy
import os
import Constants.StringConstants as Constants
from BE.BotBE import BotBE
from Utils.NetworkUtils import NetworkUtils
from youtube_dl import YoutubeDL
from spotipy.oauth2 import SpotifyClientCredentials
from embeds.custom import VoiceEmbeds
from enum import Enum
from Utils.FileUtils import FileUtils
from Utils.LoggerSaver import *
"""
 Implementation of the music functionality of the Bot. Handles radio streaming, youtube/spotify streaming and playback of local mp3 files. 
"""

f = open("spotify.txt", "r")
creds = f.read().split(",")
client_credentials_manager = SpotifyClientCredentials(client_id=creds[0], client_secret=creds[1])
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
f.close()

class Query:

    def __init__(self, the_query):
        self.the_query = the_query

    def __repr__(self):
        return self.the_query

class YoutubeQuery(Query):

    def __init__(self, the_query):
        super().__init__(the_query)

    def __repr__(self):
        return f'Busqueda de youtube: `{" ".join(self.the_query)}`'

class SpotifyQuery(Query):

    def __init__(self, the_query):
        super().__init__(the_query)


class StreamingType(Enum):
    YOUTUBE = 1
    SPOTIFY = 2

class LocalfileSource(discord.PCMVolumeTransformer):
    
    def __init__(self, file_name):
        super().__init__(discord.FFmpegPCMAudio(file_name), volume=1.0)

        self.file_name = file_name

class StreamSource(discord.PCMVolumeTransformer):

    def __init__(self, source,url, volume=1.0):
        super().__init__(source, volume)
        self.url = url

class RadioSource(StreamSource):

    def __init__(self, url, radio_name, volume=0.3):
        self.name = radio_name
        super().__init__(discord.FFmpegPCMAudio(url), url, volume=0.3)

class YTDLSource(discord.PCMVolumeTransformer):
    ytdl_opts = {
        'quiet': True,
        'format': 'bestaudio/best',
        'noplaylist': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'outtmpl': './music_cache/%(extractor)s-%(title)s.%(ext)s',
        'restrictfilenames': True,
        #'simulate': True,
        'nooverwrites': True,
        #'skip_download': False,
        'logtostderr': False,
        'keepvideo': False,
        'socket_timeout': 10,
        'no_warnings': True,
        'default_search': 'auto',
        'source_address': '0.0.0.0'
    }

    ffmpeg_options = {
        'options': '-vn'
    }

    def __init__(self, source, data, volume=0.3):
        super().__init__(source, volume)
        self.title = data.get('title')
        self.duration = self.parse_duration(int(data.get('duration')))
        self.url = data.get('webpage_url')
        self.filename = data.get('filename_vid')

    @staticmethod
    def parse_duration(duration: int):
        minutes, seconds = divmod(duration, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)

        duration = []
        if days > 0:
            duration.append('{} dias'.format(days))
        if hours > 0:
            duration.append('{} horas'.format(hours))
        if minutes > 0:
            duration.append('{} minutos'.format(minutes))
        if seconds > 0:
            duration.append('{} segundos'.format(seconds))

        return ', '.join(duration)

    @classmethod
    def from_query(cls, query, loop=None, volume=0.3):
        loop = loop or asyncio.get_event_loop()
        query = " ".join(query)
        with YoutubeDL(YTDLSource.ytdl_opts) as ydl:
            info = ydl.extract_info(query, download=False)
            if 'entries' in info:  # grab the first video
                info = info['entries'][0]

            if not info['is_live']:
                data = ydl.extract_info(query)  # TODO run in executor?
            else:
                pass  #TODO get next video

            if 'entries' in data:  # if we get a playlist, grab the first video TODO does ytdl_opts['noplaylist'] prevent this error?
                data = data['entries'][0]
            path = ydl.prepare_filename(data)
            data["filename_vid"] = path
            return cls(discord.FFmpegPCMAudio(path, **YTDLSource.ffmpeg_options), data, volume)

class VoiceManager:

    """
    The manager of a voice connection in a given guild. Delegates voice functions and commands to any given state
    (radio, streaming, speaking and saluting). 
    """

    def __init__(self, client):
        self.client = client
        self.off = Off(self, client)
        self.radio = Radio(self, client)
        self.stream = Stream(self, client)
        self.speak = Speak(self, client)
        self.salute = Salute(self, client)
        self.state = self.off
        self.prev_state = self.state
        self.voice_client = None

    def change_state(self, state):
        self.state = state

    def play(self, query, **kwargs):
        logging.warning(f"In state {self.state}")
        self.state.reproduce(query, **kwargs)

    def resume_previous(self):
        logging.warning(f"In state {self.state}")
        self.state.resume()

    def interrupt_player(self):
        if self.voice_client and self.current_player:
            self.state.should_exit_from_loop = True
            self.current_player.stop()

    def next_for_queue(self):
        if self.voice_client and self.current_player:
            self.current_player.stop()

    def pause_player(self):
        if self.voice_client and self.current_player:
            self.current_player.pause()

    def pause(self):
        if self.voice_client != None:
            self.voice_client.pause()

    def resume(self):
        if self.voice_client != None:
            self.voice_client.resume()

    def trigger_shuffle(self):
        self.state.shuffle_queue()

    def trigger_loop(self):
        self.state.trigger_loop = not self.state.trigger_loop

    def is_voice_client_playing(self):
        return self.voice_client and self.voice_client.is_playing()

    def set_volume_for_voice_client(self, volume):
        self.state.set_volume(volume)

    async def disconnect(self):
        if self.voice_client:
            logging.warning(f"Disconnected from channel {self.voice_client.channel}")
            self.state.cleanup()
            await self.voice_client.disconnect(force=True)
            self.voice_client = None
                

class State(object):

    """
    Abstract State base. Subclasses that inherit from this class represent any given voice state the bot is in. 
    """

    name = "state"

    def __init__(self, voice_manager, client):
        self.voice_manager = voice_manager
        self.client = client
        self.should_exit_from_loop = False
        self.trigger_loop = False

    def switch(self, state):
        self.voice_manager.change_state(state)

    def reproduce(self, query, **kwargs):
        """
        Starts the playback. 
        :param query is the query that the player plays. Depending on the state that inherits from this class, the query is processed accordingly.
        """
        pass

    def resume(self):
        """
        This function is called whenever the current state is interrupted by another state. Upon termination of
        the interrupting state this function is called.
        """
        pass

    def set_volume(self, volume):
        if self.voice_manager.voice_client:
            self.voice_manager.voice_client.source.volume = volume

    def cleanup(self):
        self.switch(self.voice_manager.off)
        self.voice_manager.prev_state = self.voice_manager.state

    def __str__(self):
        return self.name 

class Off(State):

    name = "off"

    def __init__(self, voice_manager, client):
        super().__init__(voice_manager, client)

    def reproduce(self, query, **kwargs):
        logging.warning("Unable to reproduce because of state OFF")
        self.client.loop.create_task(self.voice_manager.disconnect())

    def switch(self, state):
        super(Off, self).switch(state)

class Radio(State):

    name = "radio"

    def __init__(self, voice_manager, client):
        super().__init__(voice_manager, client)

    def reproduce(self, query, **kwargs):
        self.voice_manager.voice_client.play(RadioSource(query, kwargs["radio_name"]), after=lambda e: self.handle_error(e))
        self.voice_manager.current_player = self.voice_manager.voice_client._player

    def resume(self):
        if self.voice_manager.current_player:
            self.voice_manager.current_player.resume()
            self.voice_manager.voice_client._player = self.voice_manager.current_player

    def set_volume(self, volume):
        if self.voice_manager.current_player:
            self.voice_manager.current_player.source.volume = volume

    def handle_error(self, error):
        if error:
            self.client.loop.create_task(self.current_context.send("Se produjo un error"))
        if not self.should_exit_from_loop:
            self.cleanup()
        self.should_exit_from_loop = False
            
    def switch(self, state):
        self.voice_manager.pause_player()
        super(Radio, self).switch(state)
    

class Stream(State):

    name = "stream"

    def __init__(self, voice_manager, client):
        super().__init__(voice_manager, client)
        self.queue = []
        self.last_query = None
        self.current_volume = 0.3
    
    def reproduce(self, query, **kwargs):
        self.should_exit_from_loop = False
        self.original_msg = kwargs["original_msg"]
        self.queue.extend(query) if type(query) in [list] else self.queue.append(query)
        if not self.voice_manager.is_voice_client_playing():
            self.music_loop(error=None)

    def shuffle_queue(self):
        if len(self.queue) > 0:
            random.shuffle(self.queue)

    def resume(self):
        if self.voice_manager.current_player:
            self.voice_manager.current_player.resume()
            self.voice_manager.voice_client._player = self.voice_manager.current_player

    def set_volume(self, volume):
        if self.voice_manager.current_player:
            self.voice_manager.current_player.source.volume = volume
            self.current_volume = volume

    def retrieve_query_for_source(self):
        if self.trigger_loop:
            return self.last_query
        return self.queue.pop()

    def remove_video_file(self):
        if isinstance(self.voice_manager.voice_client.source, YTDLSource):
            to_delete_source = self.voice_manager.voice_client.source
            logging.debug(f"Deleting source filename {to_delete_source.filename}")
            FileUtils.delete_file(to_delete_source.filename)

    def format_embed(self):
        data = {
                'title': f'Reproduciendo {self.voice_manager.voice_client.source.title}',
                'url': self.voice_manager.voice_client.source.url,
                'author': {
                    "name": self.voice_manager.current_context.author.display_name
                },
                'fields': [
                    {
                        "name": "Duracion",
                        "value": str(self.voice_manager.voice_client.source.duration),
                        "inline": True
                    },
                    {
                        "name": "Canciones en lista",
                        "value": str(len(self.queue)),
                        "inline": False
                    }
                ]

            }
        return VoiceEmbeds.from_dict(data)

    def edit_msg(self):
        asyncio.run_coroutine_threadsafe(self.original_msg.edit(embed=self.format_embed()), self.client.loop)

    async def next_interim_msg(self):
        msg = await self.voice_manager.current_context.send("Siguiente en la lista de reproduccion...")
        self.original_msg = msg

    def music_loop(self, error):
        if self.should_exit_from_loop:
            return
        if error:
            self.cleanup()
            return
        if len(self.queue) == 0:
            msg = "Fin de la lista de reproduccion"
            asyncio.run_coroutine_threadsafe(self.voice_manager.current_context.send(msg), self.client.loop)
            asyncio.run_coroutine_threadsafe(self.voice_manager.disconnect(), self.client.loop)
            return
        if self.voice_manager.voice_client.source:
            self.remove_video_file()
        query = self.retrieve_query_for_source()
        self.last_query = query
        try:
            self.voice_manager.voice_client.play(YTDLSource.from_query(query.the_query, self.client.loop, self.current_volume), after=lambda e: self.music_loop(e))
            self.voice_manager.current_player = self.voice_manager.voice_client._player
            self.edit_msg()
        except discord.ClientException as e:
            self.cleanup()
            log = "while streaming"
            logging.error(log, exc_info=True)
            LoggerSaver.save_log(f"{log} {str(e)}", WhatsappLogger())
        except Exception as e:
            error_msg = f"Se produjo un error reproduciendo {self.voice_manager.voice_client.source.title}, intentando reproducir siguiente canción en lista"
            asyncio.run_coroutine_threadsafe(self.voice_manager.current_context.send(error_msg), self.client.loop)
            self.music_loop(error=None)
            log = "while streaming, skipping to next song"
            logging.error(log, exc_info=True)
            LoggerSaver.save_log(f"{log} {str(e)}", WhatsappLogger())

    def cleanup(self):
        super(Stream, self).cleanup()
        self.remove_video_file()
        self.queue = []
        self.trigger_loop = False
        self.shuffle_for_queue = False

class Speak(State):

    name = "speak"

    def __init__(self, voice_manager, client):
        super().__init__(voice_manager, client)

    def reproduce(self, url, **kwargs):
        voice_client = self.voice_manager.voice_client
        if isinstance(self.voice_manager.prev_state, Off):
            voice_client.play(StreamSource(discord.FFmpegPCMAudio(url), url), after= lambda e: self.switch(self.voice_manager.off))
        else:
            voice_client.play(StreamSource(discord.FFmpegPCMAudio(url), url), after= lambda e: self.resume_playing_for_prev_state(e))

    def resume_playing_for_prev_state(self, error):
        if error:
            self.switch(self.voice_manager.off)
            return
        self.switch(self.voice_manager.prev_state)
        self.voice_manager.resume_previous()

    def switch(self, state):
        super(Speak, self).switch(state)
        if isinstance(state, Off):
            self.client.loop.create_task(self.voice_manager.disconnect())

class Salute(State):

    name = "salute"

    def __init__(self, voice_manager, client):
        super().__init__(voice_manager, client)
        self.welcome_audios_queue = []

    def reproduce(self, query, **kwargs):
        voice_client = self.voice_manager.voice_client
        self.welcome_audios_queue.append(LocalfileSource(query))
        if not self.voice_manager.is_voice_client_playing():
            self.salute_loop(error=None)
        
    def salute_loop(self, error):
        if error:
            self.cleanup()
            return
        if len(self.welcome_audios_queue) == 0:
            if isinstance(self.voice_manager.prev_state, Off):
                asyncio.run_coroutine_threadsafe(self.voice_manager.disconnect(), self.client.loop)
                return
            else:
                self.switch(self.voice_manager.prev_state)
                self.resume_playing_for_prev_state(error)
                return
        source = self.welcome_audios_queue.pop()
        try:
            self.voice_manager.voice_client.play(source, after=lambda e: self.salute_loop(e))
        except discord.ClientException:
            log = "while welcoming audio"
            logging.error(log, exc_info=True)
            LoggerSaver.save_log(f"{log} {str(e)}", WhatsappLogger())
            self.cleanup()

    def resume_playing_for_prev_state(self, error):
        if error:
            self.cleanup()
            return
        self.switch(self.voice_manager.prev_state)
        self.voice_manager.resume_previous()

class Voice():
    
    OPUS_LIBS = ['libopus-0.x86.dll', 'libopus-0.x64.dll', 'libopus-0.dll', 'libopus.so.0', 'libopus.0.dylib']
    
    def __init__(self, client):
        self.client = client
        self.bot_be = BotBE()
        self.load_opus_libs()
        self.guild_to_voice_manager_map = {}
        self.populate_voice_managers()

    def populate_voice_managers(self):
        for guild in self.client.guilds:
            if guild not in self.guild_to_voice_manager_map:
                self.guild_to_voice_manager_map[guild.id] = VoiceManager(self.client)
            
    async def _set_welcome_audio_status(self, chat_channel, status: bool):
        message = chat_channel.message
        user_ids_to_audio_map = self.bot_be.load_users_welcome_audios()
        user_id = str(message.author.id)
        guild_id = str(message.author.guild.id)
        if user_id in user_ids_to_audio_map:
            user_ids_to_audio_map[user_id][guild_id]["active"] = status
            self.bot_be.save_users_welcome_audios(user_ids_to_audio_map)
            await chat_channel.send(Constants.SALUTE) if status else \
                await chat_channel.send(Constants.NOT_MORE_SALUTE)

    async def deactivate_welcome_audio(self, chat_channel):
        await self._set_welcome_audio_status(chat_channel, False)

    async def activate_welcome_audio(self, chat_channel):
        await self._set_welcome_audio_status(chat_channel, True)
            
    async def notify_subscribers_user_joined_voice_chat(self, member, voice_channel):
        members_to_notify = self.bot_be.retrieve_subscribers_from_subscribee(str(member.id))
        for member_id in members_to_notify:
            a_member = await self.client.fetch_user(member_id)
            if a_member != None:
                dm_channel = await a_member.create_dm()
                await dm_channel.send(f"{member.display_name} {Constants.HAS_ENTERED_CHANNEL} {voice_channel.name}")

    def get_stream_queue_size(self, ctx):
        vmanager = self.guild_to_voice_manager_map.get(ctx.guild.id)
        if isinstance(vmanager.state, Stream):
            return len(vmanager.state.queue)
        return 0

    def get_queue(self, ctx):
        vmanager = self.guild_to_voice_manager_map.get(ctx.guild.id)
        if isinstance(vmanager.state, Stream):
            return vmanager.state.queue
        return []

    def trigger_shuffle(self, ctx):
        vmanager = self.guild_to_voice_manager_map.get(ctx.guild.id)
        vmanager.trigger_shuffle()

    def trigger_loop_for_song(self, ctx):
        vmanager = self.guild_to_voice_manager_map.get(ctx.guild.id)
        vmanager.trigger_loop()
        return vmanager.state.trigger_loop

    def get_playing_state(self, ctx):
        return self.guild_to_voice_manager_map.get(ctx.guild.id).state

    async def next_in_queue(self, ctx):
        vmanager = self.guild_to_voice_manager_map.get(ctx.guild.id)
        msg = await vmanager.state.next_interim_msg()
        return vmanager.next_for_queue()

    def set_volume(self, volume, ctx):
        vmanager = self.guild_to_voice_manager_map.get(ctx.guild.id)
        vmanager.set_volume_for_voice_client(volume / 100.0)

    async def disconnect_player(self, ctx):
        vmanager = self.guild_to_voice_manager_map.get(ctx.guild.id)
        await vmanager.disconnect()

    def pause_player(self, ctx):
        vmanager = self.guild_to_voice_manager_map.get(ctx.guild.id)
        vmanager.pause()

    def resume_player(self, ctx):
        vmanager = self.guild_to_voice_manager_map.get(ctx.guild.id)
        vmanager.resume()

    async def reproduce_from_file(self, member, audio_filename):
        vmanager = self.guild_to_voice_manager_map.get(member.guild.id)
        try:
            vc = member.voice.channel
            if discord.opus.is_loaded():
                await self._attempt_to_connect_to_voice(vc, vmanager)
                if not await self._voice_state_check(vc, vmanager):
                    return
                if isinstance(vmanager.state, Stream) or isinstance(vmanager.state, Radio):
                    vmanager.pause_player()
                    vmanager.prev_state = vmanager.state
                if not isinstance(vmanager.state, Speak) or not isinstance(vmanager.state, Salute):
                    vmanager.change_state(vmanager.speak)
                    vmanager.play(audio_filename)
        except discord.ClientException as e:
            log = "While reproducing from file"
            logging.error(log, exc_info=True)
            LoggerSaver.save_log(f"{log} {str(e)}", WhatsappLogger())
            await vmanager.disconnect()

    async def play_welcome_audio(self, member, voice_channel):
        guild_id = member.guild.id
        vmanager = self.guild_to_voice_manager_map.get(guild_id)
        try:  
            user_ids_to_audio_map = self.bot_be.load_users_welcome_audios()
            if not str(member.id) in user_ids_to_audio_map or not user_ids_to_audio_map[str(member.id)][str(guild_id)]["active"] \
                    or not str(guild_id) in user_ids_to_audio_map[str(member.id)]:
                return
            audio_files_list = user_ids_to_audio_map[str(member.id)][str(guild_id)]["audios"]
            random_idx = random.randint(0, len(audio_files_list) - 1)
            audio_file_name = audio_files_list[random_idx]
            if discord.opus.is_loaded():
                await self._attempt_to_connect_to_voice(voice_channel, vmanager)
                if not await self._voice_state_check(voice_channel, vmanager):
                    return
                if isinstance(vmanager.state, Stream) or isinstance(vmanager.state, Radio):
                    vmanager.pause_player()
                    vmanager.prev_state = vmanager.state
                if not isinstance(vmanager.state, Speak):
                    vmanager.change_state(vmanager.salute)
                    vmanager.play(audio_file_name)
        except KeyError:
            pass
        except discord.ClientException as e:
            await vmanager.disconnect()
            log = "While welcoming audio"
            logging.error(log, exc_info=True)
            LoggerSaver.save_log(f"{log} {str(e)}", WhatsappLogger())

    async def play_radio(self, url, ctx, radio_name):
        vmanager = self.guild_to_voice_manager_map.get(ctx.guild.id)
        try:
            vc = ctx.author.voice.channel
            if discord.opus.is_loaded():
                await self._attempt_to_connect_to_voice(vc, vmanager)
                if not await self._voice_state_check(vc, vmanager, ctx):
                    return
                net_utils = NetworkUtils()
                status, content_type = await net_utils.website_check(url)
                if status != 200:
                    await ctx.send(f"Se jodio esta radio {url}")
                    return
                if isinstance(vmanager.state, Stream) or isinstance(vmanager.state, Radio):
                    vmanager.interrupt_player()
                vmanager.prev_state = vmanager.state
                vmanager.change_state(vmanager.radio)
                vmanager.current_context = ctx
                options = {'title': f'Reproduciendo radio {radio_name}'}
                msg = await ctx.send(embed=VoiceEmbeds(ctx.author,**options)) 
                vmanager.play(url, **{ "original_msg": msg, "radio_name": radio_name })
        except discord.ClientException as e:
            await vmanager.disconnect()
            log = "While playing radio"
            logging.error(log, exc_info=True)
            LoggerSaver.save_log(f"{log} {str(e)}", WhatsappLogger())

    async def play_streaming(self, query, streaming_type, ctx):
        vmanager = self.guild_to_voice_manager_map.get(ctx.guild.id)
        try:
            vc = ctx.author.voice.channel
            if discord.opus.is_loaded():
                await self._attempt_to_connect_to_voice(vc, vmanager)
                if not await self._voice_state_check(vc, vmanager, ctx):
                    return
                if isinstance(vmanager.state, Radio):
                    vmanager.interrupt_player()
                vmanager.prev_state = vmanager.state
                vmanager.change_state(vmanager.stream)
                vmanager.current_context = ctx
                if streaming_type == StreamingType.SPOTIFY:
                    await self._play_streaming_spotify(query, vmanager, ctx)
                elif streaming_type == StreamingType.YOUTUBE:
                    await self._play_streaming_youtube(query, vmanager, ctx)
        except discord.ClientException as e:
            await vmanager.disconnect()
            log = "While attempting to stream"
            logging.error(log, exc_info=True)
            LoggerSaver.save_log(f"{log} {str(e)}", WhatsappLogger())
                
    async def _play_streaming_youtube(self, query, vmanager, ctx):
        embed_options = {'title': f'Agregando a lista de reproduccion con busqueda: {" ".join(query)}'}
        msg = await ctx.send(embed=VoiceEmbeds(author=ctx.author, **embed_options))
        vmanager.play(YoutubeQuery(query), **{"original_msg": msg})

    async def _play_streaming_spotify(self, query, vmanager, ctx):
        query_list = self._process_query_object_for_spotify_playlist(query)
        if len(query_list) > 0:
            options = {'title': f'Se agregaron {len(query_list)} canciones a la lista de reproduccion'}
            msg = await ctx.send(embed=VoiceEmbeds(ctx.author,**options))
            vmanager.play(query_list, **{"original_msg": msg})
        else:
            await ctx.send("Hubo un error")
            vmanager.prev_state = vmanager.off
            vmanager.change_state(vmanager.off)

    async def _attempt_to_connect_to_voice(self, voice_channel, vmanager):
        vc_found = False
        for vc in self.client.voice_clients:
            if vc.guild.id == voice_channel.guild.id:
                vc_found = True
                break
        if not vc_found:
            vmanager.voice_client = await voice_channel.connect()

    async def _voice_state_check(self, voice_channel, vmanager,  ctx=None):
        valid = True
        if not vmanager.voice_client:
            return False
        if vmanager.voice_client.channel != voice_channel:
            if ctx:
                await ctx.send(f"No estoy en el canal {voice_channel}")
            valid = False
        return valid

    def _process_query_object_for_spotify_playlist(self, query):
        query_tracks_list = []
        try:
            results = sp.playlist(query)
            items_list = results['tracks']['items']
            for item in items_list:
                query_for_yt = ""
                a_item = item["track"]
                query_for_yt = a_item["name"] + " "
                for artist in a_item["artists"]:
                    query_for_yt += artist["name"] + " "
                query_tracks_list.append(SpotifyQuery(query_for_yt))
            return query_tracks_list
        except Exception as e:
            log = "While parsing spotify playlist"
            logging.error(log, exc_info=True)
            LoggerSaver.save_log(f"{log} {str(e)}", WhatsappLogger())
            return query_tracks_list

    def load_opus_libs(self, opus_libs=OPUS_LIBS):
        if discord.opus.is_loaded():
            return True
        for opus_lib in opus_libs:
            try:
                discord.opus.load_opus(opus_lib)
                return True
            except OSError:
                pass
        logging.error("Could not load opus lib")
        return False

    def entered_voice_channel(self, before, after):
        if after.channel and before.channel:
            return before.channel.name != after.channel.name
        return after.channel and before.channel == None

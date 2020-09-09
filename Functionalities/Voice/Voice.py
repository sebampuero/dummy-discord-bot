import asyncio
import discord
import random
import logging
import spotipy
import json
from Functionalities.Voice.VoiceQuery import *
from Functionalities.Voice.VoiceSource import *
from Functionalities.Voice.VoiceState import *
import Constants.StringConstants as Constants
from BE.BotBE import BotBE
from Utils.NetworkUtils import NetworkUtils
from spotipy.oauth2 import SpotifyClientCredentials
from embeds.custom import VoiceEmbeds
from enum import Enum
from Utils.LoggerSaver import *
"""
 Implementation of the music functionality of the Bot. Handles radio streaming, youtube/spotify streaming and playback of local mp3 files. 
"""

with open("./config/creds.json", "r") as f:
    creds = json.loads(f.read())
    client_credentials_manager = SpotifyClientCredentials(client_id=creds["spotify"]["client_id"], client_secret=creds["spotify"]["client_secret"])
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
    soundcloud_client = soundcloud.Client(client_id=creds["soundcloud"])

class StreamingType(Enum):

    def __str__(self):
        return str(self.value)

    YOUTUBE = 1
    SPOTIFY = 2
    SOUNDCLOUD = 3
    MP3_FILE = 4
    BULK_FAVS = 5

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
            await self.voice_client.disconnect(force=True)
            self.voice_client = None

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
        try:
            user_ids_to_audio_map[user_id][guild_id]["active"] = status
            self.bot_be.save_users_welcome_audios(user_ids_to_audio_map)
            await chat_channel.send(Constants.SALUTE) if status else \
                await chat_channel.send(Constants.NOT_MORE_SALUTE)
        except KeyError:
            await chat_channel.send("No tienes un saludo configurado")

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
        await vmanager.state.next_interim_msg()
        return vmanager.next_for_queue()

    def set_volume(self, volume, ctx):
        vmanager = self.guild_to_voice_manager_map.get(ctx.guild.id)
        vmanager.set_volume_for_voice_client(volume / 100.0)

    async def disconnect_player(self, ctx):
        vmanager = self.guild_to_voice_manager_map.get(ctx.guild.id)
        vmanager.state.cleanup()

    def pause_player(self, ctx):
        vmanager = self.guild_to_voice_manager_map.get(ctx.guild.id)
        vmanager.pause()

    def resume_player(self, ctx):
        vmanager = self.guild_to_voice_manager_map.get(ctx.guild.id)
        vmanager.resume()

    async def reproduce_from_file(self, member, audio_filename):
        vmanager = self.guild_to_voice_manager_map.get(member.guild.id)
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

    async def play_welcome_audio(self, member, voice_channel):
        guild_id = member.guild.id
        vmanager = self.guild_to_voice_manager_map.get(guild_id)
        try:  
            user_ids_to_audio_map = self.bot_be.load_users_welcome_audios()
            if not user_ids_to_audio_map[str(member.id)][str(guild_id)]["active"]:
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

    async def play_radio(self, url, ctx, radio_name):
        vmanager = self.guild_to_voice_manager_map.get(ctx.guild.id)
        vc = ctx.author.voice.channel
        if discord.opus.is_loaded():
            net_utils = NetworkUtils()
            status, content_type = await net_utils.website_check(url)
            if status != 200:
                return await ctx.send(f"Se jodio esta radio {url}")
            await self._attempt_to_connect_to_voice(vc, vmanager)
            if not await self._voice_state_check(vc, vmanager, ctx):
                return
            if isinstance(vmanager.state, Stream) or isinstance(vmanager.state, Radio):
                vmanager.interrupt_player()
            vmanager.prev_state = vmanager.state
            vmanager.change_state(vmanager.radio)
            vmanager.current_context = ctx
            options = {'title': f'Reproduciendo radio {radio_name}'}
            msg = await ctx.send(embed=VoiceEmbeds(ctx.author,**options)) 
            vmanager.play(url, **{ "original_msg": msg, "radio_name": radio_name })

    async def play_streaming(self, query, streaming_type, ctx):
        vmanager = self.guild_to_voice_manager_map.get(ctx.guild.id)
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
            elif streaming_type == StreamingType.SOUNDCLOUD:
                await self._play_streaming_soundcloud(query, vmanager, ctx)
            elif streaming_type == StreamingType.MP3_FILE:
                await self._play_streaming_mp3file(query, vmanager, ctx)
            elif streaming_type ==  StreamingType.BULK_FAVS:
                await self._play_streaming_bulk_favs(query, vmanager, ctx)

    async def _play_streaming_bulk_favs(self, query, vmanager, ctx):
        query_list = self._process_favorite_song_queries(query)
        embed_options = {'title': f'Agregando {len(query_list)} favoritos de {ctx.author.name}'}
        msg = await ctx.send(embed=VoiceEmbeds(author=ctx.author, **embed_options))
        vmanager.play(query_list, **{"original_msg": msg})

    def _process_favorite_song_queries(self, queries):
        query_list = []
        for item_dict in queries:            
            if int(item_dict["type"]) == int(StreamingType.SOUNDCLOUD.value):
                query_list.append(SoundcloudQuery(item_dict["query"]))
            else:
                query_list.append(YoutubeQuery(item_dict["query"]))
        return query_list

    async def _play_streaming_mp3file(self, query, vmanager, ctx):
        embed_options = {'title': f'Agregando audio de {ctx.author.display_name}'}
        msg = await ctx.send(embed=VoiceEmbeds(author=ctx.author, **embed_options))
        vmanager.play(LocalMP3Query(query.filename, query.url, ctx.author.display_name), **{"original_msg": msg})
          
    async def _play_streaming_youtube(self, query, vmanager, ctx):
        embed_options = {'title': f'Agregando a lista de reproduccion con busqueda: {" ".join(query)}'}
        msg = await ctx.send(embed=VoiceEmbeds(author=ctx.author, **embed_options))
        vmanager.play(YoutubeQuery(query), **{"original_msg": msg})

    async def _play_streaming_soundcloud(self, query, vmanager, ctx):
        embed_options = {'title': f'Agregando a lista de reproduccion con busqueda: {query}'}
        msg = await ctx.send(embed=VoiceEmbeds(author=ctx.author, **embed_options))
        vmanager.play(SoundcloudQuery(query), **{"original_msg": msg})

    async def _play_streaming_spotify(self, query, vmanager, ctx):
        query_list = self._process_query_object_for_spotify_playlist(query)
        if len(query_list) > 0:
            options = {'title': f'Se agregaron {len(query_list)} canciones a la lista de reproduccion'}
            msg = await ctx.send(embed=VoiceEmbeds(ctx.author,**options))
            vmanager.play(query_list, **{"original_msg": msg})
        else:
            await ctx.send("Error leyendo la lista de spotify")

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

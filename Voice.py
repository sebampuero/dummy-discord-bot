import asyncio
import discord
import random
import logging
import spotipy
from BE.BotBE import BotBE
import Constants.StringConstants as Constants
from Utils.NetworkUtils import NetworkUtils
from youtube_dl import YoutubeDL
from spotipy.oauth2 import SpotifyClientCredentials
from embeds.custom import VoiceEmbeds
"""
 This class is responsible for all voice communications the Bot handles (voice updates and voice output)
"""

f = open("spotify.txt", "r")
creds = f.read().split(",")
client_credentials_manager = SpotifyClientCredentials(client_id=creds[0], client_secret=creds[1])
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
f.close()

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
        'default_search': 'auto',
        'noplaylist': True,
        'quiet': True,
        # 'logger' : 'the logger'
        'format': 'bestaudio/best',
        'restrictfilenames': True,
        'outtmpl': '../music_cache/%(extractor)s-%(title)s.%(ext)s',  # %(title)s.%(ext)s',
    }

    def __init__(self, source, data, volume=0.3):
        super().__init__(source, volume)
        self.title = data.get('title')

    @classmethod
    def from_query(cls, query):
        query = ' '.join(query)
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
            return cls(discord.FFmpegPCMAudio(path), data)

class VoiceManager:

    def __init__(self, client):
        self.client = client
        self.off = Off(self, client)
        self.radio = Radio(self, client)
        self.stream = YoutubeStream(self, client)
        self.speak = Speak(self, client)
        self.salute = Salute(self, client)
        self.spotify = SpotifyStream(self, client)
        self.state = self.off
        self.prev_state = self.state
        self.voice_client = None

    def change_state(self, state):
        self.state = state

    async def play(self, query):
        logging.warning(f"In state {self.state}")
        await self.state.reproduce(query)

    async def resume(self):
        logging.warning(f"In state {self.state}")
        await self.state.resume()

    def stop_player(self):
        if self.voice_client != None:
            self.voice_client.stop()

    def pause_player(self):
        if self.voice_client != None:
            self.voice_client.pause()

    def resume_player(self):
        if self.voice_client != None:
            self.voice_client.resume()

    def is_voice_client_playing(self):
        return self.voice_client and self.voice_client.is_playing()

    def set_volume_for_voice_client(self, volume):
        self.voice_client.source.volume = volume

    async def disconnect(self):
        if self.voice_client != None:
            if self.voice_client.is_connected():
                logging.warning(f"Disconnected from channel {self.voice_client.channel}")
                await self.voice_client.disconnect()
                self.state = self.off
                self.voice_manager.prev_state = self.state

class State(object):

    name = "state"

    def __init__(self, voice_manager, client):
        self.voice_manager = voice_manager
        self.client = client

    def switch(self, state):
        self.voice_manager.change_state(state)

    async def reproduce(self, query):
        pass

    async def resume(self):
        pass

    def __str__(self):
        return self.name 

class Off(State):

    name = "off"

    def __init__(self, voice_manager, client):
        super().__init__(voice_manager, client)

    async def reproduce(self, query):
        logging.warning("Unable to reproduce because of state OFF")
        await self.voice_manager.disconnect()

    def switch(self, state):
        super(Off, self).switch(state)

    async def resume(self):
        raise NotImplementedError()

class Radio(State):

    name = "radio"

    def __init__(self, voice_manager, client):
        super().__init__(voice_manager, client)

    async def reproduce(self, query):
        voice_client = self.voice_manager.voice_client
        self.voice_manager.current_streaming_source = RadioSource(query, "")
        voice_client.play(self.voice_manager.current_streaming_source, after=lambda e: self.handle_error(e))

    async def resume(self):
        voice_client = self.voice_manager.voice_client
        if self.voice_manager.current_streaming_source:
            voice_client.play(self.voice_manager.current_streaming_source, after=lambda e: self.handle_error(e))

    def handle_error(self, error):
        self.switch(self.voice_manager.off)
        self.voice_manager.prev_state = self.voice_manager.state
            

    def switch(self, state):
        self.voice_manager.pause_player()
        super(Radio, self).switch(state)
    

class SpotifyStream(State):

    name = "spotify_stream"

    def __init__(self, voice_manager, client):
        super().__init__(voice_manager, client)
        self.queue = []
    
    async def reproduce(self, query):
        voice_client = self.voice_manager.voice_client
        self.queue = query
        if not self.voice_manager.is_voice_client_playing():
            self.music_loop(error=None)

    async def resume(self):
        voice_client = self.voice_manager.voice_client
        if self.voice_manager.current_streaming_source:
            voice_client.play(self.voice_manager.current_streaming_source, after=lambda e: self.music_loop(e))

    def music_loop(self, error):
        if error:
            self.switch(self.voice_manager.off)
            self.voice_manager.prev_state = self.voice_manager.state
            return
        if len(self.queue) == 0:
            self.switch(self.voice_manager.off)
            asyncio.run_coroutine_threadsafe(self.voice_manager.play(None), self.client.loop)
            return
        track_obj = self.queue.pop()
        query_for_yt = track_obj["name"] + " "
        for artist in track_obj["artists"]:
            query_for_yt += artist["name"] + " "
        try:
            self.voice_manager.current_streaming_source = YTDLSource.from_query(query_for_yt)
            self.voice_manager.voice_client.play(self.voice_manager.current_streaming_source, after=lambda e: self.music_loop(e))
            options = {'title': f'Reproduciendo ahora {self.voice_manager.current_streaming_source.title}'}
            embed = VoiceEmbeds(self.voice_manager.current_streaming_context.author,**options)
            asyncio.run_coroutine_threadsafe(self.voice_manager.current_streaming_context.send(embed=embed), self.client.loop)
        except discord.ClientException:
            self.switch(self.voice_manager.off)
            self.voice_manager.prev_state = self.voice_manager.state

class YoutubeStream(State):

    name = "youtube_stream"

    def __init__(self, voice_manager, client):
        super().__init__(voice_manager, client)
        self.queue = []

    async def reproduce(self, query):
        voice_client = self.voice_manager.voice_client
        self.queue.append(query)
        if not self.voice_manager.is_voice_client_playing():
            self.music_loop(error=None)

    async def resume(self):
        voice_client = self.voice_manager.voice_client
        if self.voice_manager.current_streaming_source:
            voice_client.play(self.voice_manager.current_streaming_source, after=lambda e: self.music_loop(e))

    def music_loop(self, error):
        if error:
            self.switch(self.voice_manager.off)
            self.voice_manager.prev_state = self.voice_manager.state
            return
        if len(self.queue) == 0:
            self.switch(self.voice_manager.off)
            asyncio.run_coroutine_threadsafe(self.voice_manager.play(None), self.client.loop)
            return
        query = self.queue.pop()
        self.voice_manager.current_streaming_source = YTDLSource.from_query(query)
        try:
            self.voice_manager.voice_client.play(self.voice_manager.current_streaming_source, after=lambda e: self.music_loop(e))
            options = {'title': f'Reproduciendo ahora {self.voice_manager.current_streaming_source.title}'}
            embed = VoiceEmbeds(self.voice_manager.current_streaming_context.author,**options)
            asyncio.run_coroutine_threadsafe(self.voice_manager.current_streaming_context.send(embed=embed), self.client.loop)
        except discord.ClientException:
            self.switch(self.voice_manager.off)
            self.voice_manager.prev_state = self.voice_manager.state

class Speak(State):

    name = "speak"

    def __init__(self, voice_manager, client):
        super().__init__(voice_manager, client)

    async def reproduce(self, query):
        voice_client = self.voice_manager.voice_client 
        if isinstance(self.voice_manager.prev_state, Off):
            voice_client.play(LocalfileSource(query), after= lambda e: self.switch(self.voice_manager.off))
        else:
            voice_client.play(LocalfileSource(query), after= lambda e: self.resume_playing_for_prev_state(e))

    def resume_playing_for_prev_state(self, error):
        if error:
            self.switch(self.voice_manager.off)
            return
        self.switch(self.voice_manager.prev_state)
        asyncio.run_coroutine_threadsafe(self.voice_manager.resume(), self.client.loop)

    async def resume(self):
        raise NotImplementedError()

    def switch(self, state):
        super(Speak, self).switch(state)
        if isinstance(state, Off):
            asyncio.run_coroutine_threadsafe(self.voice_manager.play(None), self.client.loop)

class Salute(State):

    name = "salute"

    def __init__(self, voice_manager, client):
        super().__init__(voice_manager, client)
        self.welcome_audios_queue = []

    async def reproduce(self, query):
        voice_client = self.voice_manager.voice_client
        self.welcome_audios_queue.append(LocalfileSource(query))
        if not self.voice_manager.is_voice_client_playing():
            self.salute_loop(error=None)
        
    def salute_loop(self, error):
        if error:
            self.switch(self.voice_manager.off)
            self.voice_manager.prev_state = self.voice_manager.state
            return
        if len(self.welcome_audios_queue) == 0:
            if isinstance(self.voice_manager.prev_state, Off):
                self.switch(self.voice_manager.off)
                asyncio.run_coroutine_threadsafe(self.voice_manager.play(None), self.client.loop)
                return
            else:
                self.switch(self.voice_manager.prev_state)
                self.resume_playing_for_prev_state(error=None)
                return
        source = self.welcome_audios_queue.pop()
        try:
            self.voice_manager.voice_client.play(source, after=lambda e: self.salute_loop(e))
        except discord.ClientException:
            self.switch(self.voice_manager.off)
            self.voice_manager.prev_state = self.voice_manager.state

    def resume_playing_for_prev_state(self, error):
        if error:
            self.switch(self.voice_manager.off)
            return
        self.switch(self.voice_manager.prev_state)
        asyncio.run_coroutine_threadsafe(self.voice_manager.resume(), self.client.loop)

    async def resume(self):
        raise NotImplementedError()

class Voice():
    
    OPUS_LIBS = ['libopus-0.x86.dll', 'libopus-0.x64.dll', 'libopus-0.dll', 'libopus.so.0', 'libopus.0.dylib']
    
    def __init__(self, client):
        self.client = client
        self.bot_be = BotBE()
        self.load_opus_libs()
        self._populate_voice_managers()

    def _populate_voice_managers(self):
        self.guild_to_voice_manager_map = {}
        for guild in self.client.guilds:
            self.guild_to_voice_manager_map[guild.id] = VoiceManager(self.client)
            
    async def deactivate_welcome_audio(self, chat_channel): #TODO: remember to use guild as object containing audio items and status
        message = chat_channel.message
        user_ids_to_audio_map = self.bot_be.load_users_welcome_audios()
        user_id = str(message.author.id)
        if user_id in user_ids_to_audio_map:
            user_ids_to_audio_map[user_id]["active"] = False
            self.bot_be.save_users_welcome_audios(user_ids_to_audio_map)
            await chat_channel.send(Constants.NOT_MORE_SALUTE)

    async def activate_welcome_audio(self, chat_channel):
        message = chat_channel.message
        user_ids_to_audio_map = self.bot_be.load_users_welcome_audios()
        user_id = str(message.author.id)
        if user_id in user_ids_to_audio_map:
            user_ids_to_audio_map[user_id]["active"] = True
            self.bot_be.save_users_welcome_audios(user_ids_to_audio_map)
            await chat_channel.send(Constants.SALUTE)
            
    async def notify_subscribers_user_joined_voice_chat(self, member, voice_channel, client):
        members_to_notify = self.bot_be.retrieve_subscribers_from_subscribee(str(member.id))
        for member_id in members_to_notify:
            a_member = await client.fetch_user(member_id)
            if a_member != None:
                dm_channel = await a_member.create_dm()
                await dm_channel.send(f"{member.display_name} {Constants.HAS_ENTERED_CHANNEL} {voice_channel.name}")
                
    async def say_good_night(self, member):
        try:
            await self.reproduce_from_file(member, "./assets/audio/vladimir.mp3")
        except Exception as e:
            logging.error("While saying good night", exc_info=True)

    def get_playing_state(self, ctx):
        return self.guild_to_voice_manager_map.get(ctx.guild.id).state

    def stop_player(self, ctx):
        vmanager = self.guild_to_voice_manager_map.get(ctx.guild.id)
        return vmanager.stop_player()

    def set_volume(self, volume, ctx):
        vmanager = self.guild_to_voice_manager_map.get(ctx.guild.id)
        vmanager.set_volume_for_voice_client(volume / 100.0)

    async def disconnect_player(self, ctx):
        vmanager = self.guild_to_voice_manager_map.get(ctx.guild.id)
        await vmanager.disconnect()

    def pause_player(self, ctx):
        vmanager = self.guild_to_voice_manager_map.get(ctx.guild.id)
        vmanager.pause_player()

    def resume_player(self, ctx):
        vmanager = self.guild_to_voice_manager_map.get(ctx.guild.id)
        vmanager.resume_player()

    async def reproduce_from_file(self, member, audio_filename):
        vmanager = self.guild_to_voice_manager_map.get(member.guild.id)
        try:
            vc = member.voice.channel
            if discord.opus.is_loaded():
                if vmanager.voice_client == None or not vmanager.voice_client.is_connected():
                    vmanager.voice_client = await vc.connect()
                if isinstance(vmanager.state, YoutubeStream) or isinstance(vmanager.state, Radio) or isinstance(vmanager.state, SpotifyStream):
                    vmanager.pause_player()
                    vmanager.prev_state = vmanager.state
                vmanager.change_state(vmanager.speak)
                await vmanager.play(audio_filename)
        except Exception as e:
            logging.error("While reproducing from file", exc_info=True)
            await vmanager.disconnect()

    async def play_welcome_audio(self, member, voice_channel):
        guild_id = member.guild.id
        vmanager = self.guild_to_voice_manager_map.get(guild_id)
        try:  
            user_ids_to_audio_map = self.bot_be.load_users_welcome_audios()
            if not str(member.id) in user_ids_to_audio_map or not user_ids_to_audio_map[str(member.id)]["active"] or not str(guild_id) in user_ids_to_audio_map[str(member.id)]:
                return
            audio_files_list = user_ids_to_audio_map[str(member.id)][str(guild_id)]
            random_idx = random.randint(0, len(audio_files_list) - 1)
            audio_file_name = audio_files_list[random_idx]
            if discord.opus.is_loaded():
                if vmanager.voice_client == None or not vmanager.voice_client.is_connected():
                    vmanager.voice_client = await voice_channel.connect()
                if isinstance(vmanager.state, YoutubeStream) or isinstance(vmanager.state, Radio) or isinstance(vmanager.state, SpotifyStream):
                    vmanager.pause_player()
                    vmanager.prev_state = vmanager.state
                if not isinstance(vmanager.state, Speak):
                    vmanager.change_state(vmanager.salute)
                    await vmanager.play(audio_file_name)
        except Exception as e:
            await vmanager.disconnect()
            logging.error("While playing welcome audio", exc_info=True)

    async def play_radio(self, url, ctx, radio_name):
        vmanager = self.guild_to_voice_manager_map.get(ctx.guild.id)
        try:
            vc = ctx.author.voice.channel
            if discord.opus.is_loaded():
                if vmanager.voice_client == None or not vmanager.voice_client.is_connected():
                    vmanager.voice_client = await vc.connect()
                if vmanager.voice_client.channel != vc:
                    await vmanager.voice_client.move_to(vc)
                net_utils = NetworkUtils()
                if await net_utils.check_connection_status_for_site(url) != 200:
                    await ctx.send(f"Se jodio esta radio {url}")
                    return
                if isinstance(vmanager.state, YoutubeStream) or isinstance(vmanager.state, Radio) or isinstance(vmanager.state, SpotifyStream):
                    vmanager.pause_player()
                vmanager.prev_state = vmanager.state
                vmanager.change_state(vmanager.radio)
                await vmanager.play(url)
                options = {'title': f'Reproduciendo radio {radio_name}'}
                embed = VoiceEmbeds(ctx.author,**options)
                await ctx.send(embed=embed)
        except Exception as e:
            await vmanager.disconnect()
            logging.error("While streaming audio", exc_info=True)

    async def play_for_youtube(self, query, ctx):
        vmanager = self.guild_to_voice_manager_map.get(ctx.guild.id)
        try:
            vc = ctx.author.voice.channel
            if discord.opus.is_loaded():
                if vmanager.voice_client == None or not vmanager.voice_client.is_connected():
                    vmanager.voice_client = await vc.connect()
                if vmanager.voice_client.channel != vc:
                    await vmanager.voice_client.move_to(vc)
                if isinstance(vmanager.state, Radio) or isinstance(vmanager.state, SpotifyStream):
                    vmanager.pause_player()
                vmanager.prev_state = vmanager.state
                vmanager.change_state(vmanager.stream)
                vmanager.current_streaming_context = ctx
                await vmanager.play(query)
        except Exception as e:
            await vmanager.disconnect()
            logging.error("While youtibing", exc_info=True)

    async def play_for_spotify(self, query, ctx):
        vmanager = self.guild_to_voice_manager_map.get(ctx.guild.id)
        try:
            vc = ctx.author.voice.channel
            if discord.opus.is_loaded():
                if vmanager.voice_client == None or not vmanager.voice_client.is_connected():
                    vmanager.voice_client = await vc.connect()
                if vmanager.voice_client.channel != vc:
                    await vmanager.voice_client.move_to(vc)
                if isinstance(vmanager.state, SpotifyStream):
                    await ctx.send("Una lista de spotify ya se esta reproduciendo")
                if isinstance(vmanager.state, Radio) or isinstance(vmanager.state, YoutubeStream):
                    vmanager.pause_player()
                query = self.process_query_object_for_spotify_playlist(query)
                vmanager.prev_state = vmanager.state
                vmanager.change_state(vmanager.spotify)
                vmanager.current_streaming_context = ctx
                if len(query) > 0:
                    await vmanager.play(query)
                    options = {'title': f'Se agregaron {len(query)} canciones a la lista de reproduccion'}
                    embed = VoiceEmbeds(ctx.author,**options)
                    await ctx.send(embed=embed)
                else:
                    await ctx.send("Hubo un error")
        except Exception as e:
            await vmanager.disconnect()
            logging.error("While streaming spotify", exc_info=True)

    def process_query_object_for_spotify_playlist(self, query):
        query_tracks_list = []
        try:
            results = sp.playlist(query)
            items_list = results['tracks']['items']
            for item in items_list:
                track_obj = {}
                a_item = item["track"]
                track_obj["name"] = a_item["name"]
                track_obj["artists"] = a_item["artists"]
                query_tracks_list.append(track_obj)
            return query_tracks_list
        except Exception as e:
            logging.error("While retrieving spotify playlist info", exc_info=True)
            return query_tracks_list

    def load_opus_libs(self, opus_libs=OPUS_LIBS):
        if discord.opus.is_loaded():
            return True
        for opus_lib in opus_libs:
            try:
                discord.opus.load_opus(opus_lib)
                return
            except OSError:
                pass         

    def entered_voice_channel(self, before, after):
        return after.channel != None and not before.self_deaf and not before.self_mute and not before.self_stream and not after.self_deaf and not after.self_mute and not after.self_stream

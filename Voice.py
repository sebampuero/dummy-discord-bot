import asyncio
import discord
import random
import logging
from BE.BotBE import BotBE
import Constants.StringConstants as Constants
from Utils.NetworkUtils import NetworkUtils
from youtube_dl import YoutubeDL
from embeds.custom import VoiceEmbeds
"""
 This class is responsible for all voice communications the Bot handles (voice updates and voice output)
"""

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
            ydl.cache.remove()
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

    COUNTER_IDLE_TIMEOUT = 1

    def __init__(self, client):
        self.client = client
        self.welcome_audios_queue = []
        self.player_queue = []
        self.idle_counter = 0
        self.started_counter_flag = False
        self.is_streaming = False
        self.is_speaking = False
        self.current_streaming_source = None
        self.current_streaming_context = None
        self.voice_client = None

    async def init_counter_voice_idle_timeout(self, counter_idle_timeout=COUNTER_IDLE_TIMEOUT):
        if not self.started_counter_flag:
            self.started_counter_flag = True
            while True:
                await asyncio.sleep(1)
                if not self.voice_client.is_playing():
                    self.idle_counter = self.idle_counter + 1
                    if self.idle_counter == counter_idle_timeout:
                        self.started_counter_flag = False
                        await self.disconnect()
                        break

    def restart_counter_voice_idle_timeout(self):
        self.idle_counter = 0

    def after_speaking(self, error):
        self.is_speaking = False
        if self.is_streaming:
            self.resume_streaming()

    def resume_streaming(self):
        if self.current_streaming_source:
            print("resuming stream")
            self.voice_client.play(self.current_streaming_source, after=lambda e: self.music_loop(e)) #does not matter if radio streams, after will never be called 
            
    def music_loop(self, error):
        if len(self.player_queue) == 0:
            return asyncio.run_coroutine_threadsafe(self.disconnect(), self.client.loop)
        source_to_play = self.player_queue.pop()
        self.current_streaming_source = source_to_play
        self.voice_client.play(source_to_play, after=lambda e: self.music_loop(e))
        options = {'title': f'Reproduciendo ahora {source_to_play.title}'}
        embed = VoiceEmbeds(self.current_streaming_context.author,**options)
        asyncio.run_coroutine_threadsafe(self.current_streaming_context.send(embed=embed), self.client.loop)

    def start_salute_loop(self, error):
        if len(self.welcome_audios_queue) == 0:
            if self.is_streaming:
                return self.after_speaking(error=None)
            else:
                return asyncio.run_coroutine_threadsafe(self.disconnect(), self.client.loop)
        source = self.welcome_audios_queue.pop()
        self.voice_client.play(source, after=lambda e: self.start_salute_loop)

    async def disconnect(self):
        if self.voice_client != None:
            if self.voice_client.is_connected():
                logging.warning(f"Disconnected from channel {self.voice_client.channel}")
                await self.voice_client.disconnect()
                self.current_streaming_source = None
                self.current_streaming_context = None
                self.is_streaming = False
                self.is_speaking = False
                
    def is_voice_client_playing(self):
        if self.voice_client != None:
            return self.voice_client.is_playing()
        return False

    def is_voice_client_speaking(self):
        return self.is_speaking

    def is_voice_client_streaming(self):
        return self.is_streaming
        
    def stop_player(self):
        if self.voice_client != None:
            self.voice_client.stop()

    def pause_player(self):
        if self.voice_client != None:
            self.voice_client.pause()

    def resume_player(self):
        if self.voice_client != None:
            self.voice_client.resume()

    def set_volume_for_voice_client(self, volume):
        self.voice_client.source.volume = volume

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
            
    async def deactivate_welcome_audio(self, chat_channel):
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

    def is_voice_speaking_for_guild(self, guild):
        vmanager = self.guild_to_voice_manager_map.get(guild.id)
        return vmanager.is_voice_client_speaking()

    def is_voice_playing_for_guild(self, guild):
        vmanager = self.guild_to_voice_manager_map.get(guild.id)
        return vmanager.is_voice_client_playing()

    def is_voice_streaming_for_guild(self, guild):
        vmanager = self.guild_to_voice_manager_map.get(guild.id)
        return vmanager.is_voice_client_streaming()

    def stop_player_for_guild(self, guild):
        vmanager = self.guild_to_voice_manager_map.get(guild.id)
        return vmanager.stop_player()

    def set_volume_for_guild(self, volume, guild):
        vmanager = self.guild_to_voice_manager_map.get(guild.id)
        vmanager.set_volume_for_voice_client(volume / 100.0)

    async def disconnect_player_for_guild(self, guild):
        vmanager = self.guild_to_voice_manager_map.get(guild.id)
        await vmanager.disconnect()

    async def reproduce_from_file(self, member, audio_filename):
        vmanager = self.guild_to_voice_manager_map.get(member.guild.id)
        try:
            vc = member.voice.channel
            if discord.opus.is_loaded():
                vmanager.restart_counter_voice_idle_timeout()
                if vmanager.voice_client == None or not vmanager.voice_client.is_connected():
                    vmanager.voice_client = await vc.connect()
                audio_source = LocalfileSource(audio_filename)
                if vmanager.is_voice_client_streaming() and vc == vmanager.voice_client.channel:
                    vmanager.pause_player()
                if not vmanager.is_voice_client_playing():
                    vmanager.is_speaking = True
                    vmanager.voice_client.play(audio_source, after=vmanager.after_speaking)
                    if not vmanager.is_voice_client_streaming():
                        await vmanager.init_counter_voice_idle_timeout()
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
                if vmanager.is_voice_client_streaming() and voice_channel != vmanager.voice_client.channel:
                    return
                if vmanager.is_voice_client_streaming():
                    vmanager.pause_player()
                source = LocalfileSource(audio_file_name)
                vmanager.welcome_audios_queue.append(source)
                if not vmanager.is_voice_client_speaking():
                    vmanager.is_speaking = True
                    vmanager.start_salute_loop
        except Exception as e:
            await vmanager.disconnect()
            logging.error("While playing welcome audio", exc_info=True)

    async def play_streaming(self, url, ctx, radio_name):
        vmanager = self.guild_to_voice_manager_map.get(ctx.guild.id)
        try:
            vc = ctx.author.voice.channel
            if discord.opus.is_loaded():
                if vmanager.voice_client == None or not vmanager.voice_client.is_connected():
                    vmanager.voice_client = await vc.connect()
                if vmanager.voice_client.channel != vc:
                    await vmanager.voice_client.move_to(vc)
                if not vmanager.is_voice_client_playing():
                    net_utils = NetworkUtils()
                    if await net_utils.check_connection_status_for_site(url) != 200:
                        await ctx.send(f"Se jodio esta radio {url}")
                        return
                    player = RadioSource(url, radio_name)
                    vmanager.current_streaming_source = player
                    vmanager.is_streaming = True
                    vmanager.voice_client.play(player)
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
                vmanager.is_streaming = True
                player_source = YTDLSource.from_query(query)
                vmanager.player_queue.append(player_source)
                vmanager.current_streaming_context = ctx
                if not vmanager.is_voice_client_playing():
                    vmanager.music_loop(error=None)
        except Exception as e:
            await vmanager.disconnect()
            logging.error("While streaming audio", exc_info=True)

    async def skip_for_youtube(self, ctx):
        vmanager = self.guild_to_voice_manager_map.get(ctx.guild.id)
        try:
            vc = ctx.author.voice.channel
            if discord.opus.is_loaded():
                if vmanager.voice_client == None or not vmanager.voice_client.is_connected():
                    return await ctx.send("Tengo que estar primero en un canal de voz")
                if vmanager.voice_client.channel != vc:
                    return await ctx.send(f"No estoy en este canal de voz {vc.name}")
                vmanager.stop_player()
        except Exception as e:
            await vmanager.disconnect()
            logging.error("While streaming audio", exc_info=True)

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
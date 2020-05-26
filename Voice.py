import asyncio
import discord
import random
import logging
from BE.BotBE import BotBE
import Constants.StringConstants as Constants
from Concurrent.FileDeleter import FileDeleterThread
from Utils.NetworkUtils import NetworkUtils
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

class Voice():
    
    OPUS_LIBS = ['libopus-0.x86.dll', 'libopus-0.x64.dll', 'libopus-0.dll', 'libopus.so.0', 'libopus.0.dylib']
    COUNTER_IDLE_TIMEOUT = 1
    
    def __init__(self, client):
        self.client = client
        self.welcome_audios_queue = []
        self.bot_be = BotBE()
        self.load_opus_libs()
        self.idle_counter = 0
        self.started_counter_flag = False
        self.is_streaming = False
        self.is_speaking = False
        self.current_streaming_url = None
        
    async def _init_counter_voice_idle_timeout(self, counter_idle_timeout=COUNTER_IDLE_TIMEOUT):
        if not self.started_counter_flag:
            self.started_counter_flag = True
            while True:
                await asyncio.sleep(1)
                if not self.client.voice_clients[0].is_playing():
                    self.idle_counter = self.idle_counter + 1
                    if self.idle_counter == counter_idle_timeout:
                        self.started_counter_flag = False
                        await self.disconnect()
                        break

    def _restart_counter_voice_idle_timeout(self):
        self.idle_counter = 0
            
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
            
    def _after_talking(self, error):
        self.is_speaking = False
        if self.is_streaming:
            self._resume_streaming()

    def _resume_streaming(self):
        if self.current_streaming_url:
            self.client.voice_clients[0].play(RadioSource(self.current_streaming_url, "")) # TODO: CHECK

    async def reproduce_from_file(self, member, audio_filename):
        try:
            vc = member.voice.channel
            member_guild = member.guild
            if discord.opus.is_loaded():
                self._restart_counter_voice_idle_timeout()
                if len(self.client.voice_clients) == 0:
                    await vc.connect()
                audio_source = LocalfileSource(audio_filename)
                if self.is_streaming and vc == self.client.voice_clients[0].channel:
                    self.stop_player()
                if not self.client.voice_clients[0].is_playing():
                    self.is_speaking = True
                    self.client.voice_clients[0].play(audio_source, after=self._after_talking)
                    if not self.is_streaming:
                        await self._init_counter_voice_idle_timeout()
        except Exception as e:
            logging.error("While reproducing from file", exc_info=True)
            await self.disconnect()
            
    async def play_welcome_audio(self, member, voice_channel):
        try:  
            member_guild = member.guild
            user_ids_to_audio_map = self.bot_be.load_users_welcome_audios()
            if not str(member.id) in user_ids_to_audio_map or not user_ids_to_audio_map[str(member.id)]["active"]:
                return
            audio_files_list = user_ids_to_audio_map[str(member.id)]["audio_files"]
            random_idx = random.randint(0, len(audio_files_list) - 1)
            audio_file_name = audio_files_list[random_idx]
            if discord.opus.is_loaded():
                self._restart_counter_voice_idle_timeout()
                if len(self.client.voice_clients) == 0:
                    await voice_channel.connect()
                first_audio_source = LocalfileSource(audio_file_name)
                if self.is_streaming and voice_channel != self.client.voice_clients[0].channel:
                    return
                if self.is_streaming:
                    self.stop_player() #TODO: Think of a better logic
                self.is_speaking = True 
                if self.client.voice_clients[0].is_playing():
                    self.welcome_audios_queue.append(first_audio_source)
                    while True:
                        if not self.client.voice_clients[0].is_playing():
                            audio_source = self.welcome_audios_queue.pop()
                            self.client.voice_clients[0].play(audio_source, after=self._after_talking)
                            if len(self.welcome_audios_queue) == 0:
                                break
                else:
                    self.client.voice_clients[0].play(first_audio_source, after=self._after_talking)
                    if not self.is_streaming:
                        await self._init_counter_voice_idle_timeout()
        except Exception as e:
            await self.disconnect()
            logging.error("While playing welcome audio", exc_info=True)

    async def play_streaming(self, url, ctx, radio_name):
        try:
            member_guild = ctx.author.guild
            vc = ctx.author.voice.channel
            if discord.opus.is_loaded():
                if len(self.client.voice_clients) == 0:
                    await vc.connect()
                if self.client.voice_clients[0].channel != vc:
                    await self.client.voice_clients[0].move_to(vc)
                if not self.client.voice_clients[0].is_playing():
                    net_utils = NetworkUtils()
                    if await net_utils.check_connection_status_for_site(url) != 200:
                        await ctx.send(f"Se jodio esta radio {url}")
                        return
                    player = RadioSource(url, radio_name)
                    self.current_streaming_url = url
                    self.is_streaming = True
                    self.client.voice_clients[0].play(player)
                    await ctx.send(f"Reproduciendo {radio_name}")
        except Exception as e:
            await self.disconnect()
            logging.error("While streaming audio", exc_info=True)
    
    async def disconnect(self):
        if len(self.client.voice_clients) > 0:
            if self.client.voice_clients[0].is_connected():
                logging.warning(f"Disconnected from channel {self.client.voice_clients[0].channel}")
                await self.client.voice_clients[0].disconnect()
                self.current_streaming_url = None
                self.is_streaming = False
                self.is_speaking = False
                
    def is_voice_client_playing(self):
        if len(self.client.voice_clients) > 0:
            return self.client.voice_clients[0].is_playing()
        return False

    def is_voice_client_speaking(self):
        return self.is_speaking

    def is_voice_client_streaming(self):
        return self.is_streaming
        
    def stop_player(self):
        if len(self.client.voice_clients) > 0:
            self.client.voice_clients[0].stop()
            
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
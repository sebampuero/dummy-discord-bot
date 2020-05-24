import os.path
import asyncio
import discord
import json
import random
import logging
import time
from BE.BotBE import BotBE
import Constants.StringConstants as Constants
from Concurrent.FileDeleter import FileDeleterThread
from Utils.NetworkUtils import NetworkUtils
"""
 This class is responsible for all voice communications the Bot handles (voice updates and voice output)
"""


class Voice():
    
    OPUS_LIBS = ['libopus-0.x86.dll', 'libopus-0.x64.dll', 'libopus-0.dll', 'libopus.so.0', 'libopus.0.dylib']
    COUNTER_IDLE_TIMEOUT = 1
    
    def __init__(self, client): #TODO: Add constant variables for volume
        #TODO: prevent changing of voice channel
        self.client = client
        self.welcome_audios_queue = []
        self.bot_be = BotBE()
        self.load_opus_libs()
        self.idle_counter = 0
        self.started_counter_flag = False
        self.is_streaming = False
        self.is_speaking = False
        self.current_streaming_ = None
        
    async def initCounterIdleTimeout(self, counter_idle_timeout=COUNTER_IDLE_TIMEOUT):
        if self.is_streaming: # dont disconnect if we are streaming radio
            return
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

    def restartCounterIdleTimeout(self):
        self.idle_counter = 0
            
    async def deactivateWelcomeAudio(self, message, chat_channel):
        user_ids_to_audio_map = self.bot_be.load_users_welcome_audios()
        user_id = str(message.author.id)
        if user_id in user_ids_to_audio_map:
            user_ids_to_audio_map[user_id]["active"] = False
            self.bot_be.save_users_welcome_audios(user_ids_to_audio_map)
            await chat_channel.send(Constants.NOT_MORE_SALUTE)

    async def activateWelcomeAudio(self, message, chat_channel):
        user_ids_to_audio_map = self.bot_be.load_users_welcome_audios()
        user_id = str(message.author.id)
        if user_id in user_ids_to_audio_map:
            user_ids_to_audio_map[user_id]["active"] = True
            self.bot_be.save_users_welcome_audios(user_ids_to_audio_map)
            await chat_channel.send(Constants.SALUTE)
            
    async def notifySubscribersUserJoinedVoiceChat(self, member, after, client):
        members_to_notify = self.bot_be.retrieve_subscribers_from_subscribee(str(member.id))
        for member_id in members_to_notify:
            a_member = await client.fetch_user(member_id)
            if a_member != None:
                dm_channel = await a_member.create_dm()
                await dm_channel.send(f"{member.display_name} {Constants.HAS_ENTERED_CHANNEL} {after.channel.name}")
                
    async def sayGoodNight(self, member):
        try:
            await self.reproduceFromFile(member, "./assets/audio/vladimir.mp3")
        except Exception as e:
            logging.error("While saying good night", exc_info=True)
            
    def afterTalking(self, error):
        self.is_speaking = False
        if self.is_streaming:
            self.resumeStreaming()

    def resumeStreaming(self):
        if self.current_streaming_url:
            self.client.voice_clients[0].play(discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(self.current_streaming_url), volume=0.5))

    async def reproduceFromFile(self, member, audio_filename):
        try:
            vc = member.voice.channel
            if discord.opus.is_loaded():
                self.restartCounterIdleTimeout()
                if len(self.client.voice_clients) == 0:
                    await vc.connect()
                audio_source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(audio_filename), volume=1.0)
                if self.is_streaming:
                    self.stopPlayer()
                if not self.client.voice_clients[0].is_playing():
                    self.is_speaking = True
                    self.client.voice_clients[0].play(audio_source, after=self.afterTalking)
                    await self.initCounterIdleTimeout()
        except Exception as e:
            logging.error("While reproducing from file", exc_info=True)
            await self.disconnect()
            
    async def playWelcomeAudio(self, member, after):
        try:
            user_ids_to_audio_map = self.bot_be.load_users_welcome_audios()
            if not str(member.id) in user_ids_to_audio_map:
                return
            if not user_ids_to_audio_map[str(member.id)]["active"]:
                return
            audio_files_list = user_ids_to_audio_map[str(member.id)]["audio_files"]
            random_idx = random.randint(0, len(audio_files_list) - 1)
            audio_file_name = audio_files_list[random_idx]
            if discord.opus.is_loaded():
                self.restartCounterIdleTimeout()
                if len(self.client.voice_clients) == 0:
                    await after.channel.connect()
                first_audio_source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(audio_file_name), volume=1.0)
                self.is_speaking = True
                if self.is_streaming:
                    self.stopPlayer()
                if self.client.voice_clients[0].is_playing():
                    self.welcome_audios_queue.append(first_audio_source)
                    while True:
                        if not self.client.voice_clients[0].is_playing():
                            audio_source = self.welcome_audios_queue.pop()
                            self.client.voice_clients[0].play(audio_source, after=self.afterTalking)
                            if len(self.welcome_audios_queue) == 0:
                                break
                else:
                    self.client.voice_clients[0].play(first_audio_source, after=self.afterTalking)
                    await self.initCounterIdleTimeout()
        except Exception as e:
            await self.disconnect()
            logging.error("While playing welcome audio", exc_info=True)

    async def playStreamingRadio(self, url, voice_channel, text_channel):
        try:
            vc = voice_channel
            if discord.opus.is_loaded():
                if len(self.client.voice_clients) == 0:
                    await vc.connect()
                if self.client.voice_clients[0].channel != voice_channel:
                    await self.client.voice_clients[0].move_to(voice_channel)
                if not self.client.voice_clients[0].is_playing():
                    net_utils = NetworkUtils()
                    if await net_utils.checkConnectionStatusForSite(url) != 200:
                        await text_channel.send(f"Se jodio esta radio {url}")
                        return
                    player = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(url), volume=0.5)
                    self.current_streaming_url = url
                    self.is_streaming = True
                    self.client.voice_clients[0].play(player)
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
                
    def isVoiceClientPlaying(self):
        if len(self.client.voice_clients) > 0:
            return self.client.voice_clients[0].is_playing()

    def isVoiceClientSpeaking(self):
        return self.is_speaking

    def isVoiceClientStreaming(self):
        return self.is_streaming
        
    def stopPlayer(self):
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

    def isVoiceStateValid(self, before, after):
        return after.channel != None and not before.self_deaf and not before.self_mute and not before.self_stream and not after.self_deaf and not after.self_mute and not after.self_stream
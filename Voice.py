import os.path
import asyncio
import discord
import json
import random
import logging
import time
from BE.BotBE import BotBE
import Constants.StringConstants as Constants
from Concurrent.StreamingThread import StreamingThread
from Concurrent.FileDeleter import FileDeleterThread
"""
 This class is responsible for all voice communications the Bot handles (voice updates and voice output)
"""


class Voice():
    
    OPUS_LIBS = ['libopus-0.x86.dll', 'libopus-0.x64.dll', 'libopus-0.dll', 'libopus.so.0', 'libopus.0.dylib']
    COUNTER_IDLE_TIMEOUT = 1
    MAX_FAILED_STREAMING_TRIES = 10
    
    def __init__(self, client):
        self.client = client
        self.welcome_audios_queue = []
        self.bot_be = BotBE()
        self.load_opus_libs()
        self.idle_counter = 0
        self.started_counter_flag = False
        self.is_streaming = False
        
    async def initCounterIdleTimeout(self, counter_idle_timeout=COUNTER_IDLE_TIMEOUT):
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
        f = open("users_audio_map.json", "r") #TODO: add consistent atomic access for this file
        user_ids_to_audio_map = json.load(f)
        f.close()
        user_id = str(message.author.id)
        if user_id in user_ids_to_audio_map:
            user_ids_to_audio_map[user_id]["active"] = False
            f = open("users_audio_map.json", "w")
            json.dump(user_ids_to_audio_map, f)
            f.close()
            await chat_channel.send(Constants.NOT_MORE_SALUTE)

    async def activateWelcomeAudio(self, message, chat_channel):
        f = open("users_audio_map.json", "r")
        user_ids_to_audio_map = json.load(f)
        f.close()
        user_id = str(message.author.id)
        if user_id in user_ids_to_audio_map:
            user_ids_to_audio_map[user_id]["active"] = True
            f = open("users_audio_map.json", "w")
            json.dump(user_ids_to_audio_map, f)
            f.close()
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
            
    async def reproduceFromFile(self, member, audio_filename):
        try:
            vc = member.voice.channel
            if discord.opus.is_loaded():
                self.restartCounterIdleTimeout()
                if len(self.client.voice_clients) == 0:
                    await vc.connect()
                audio_source = discord.FFmpegPCMAudio(audio_filename)
                if not self.client.voice_clients[0].is_playing():
                    self.client.voice_clients[0].play(audio_source)
                    await self.initCounterIdleTimeout()
        except Exception as e:
            logging.error("While reproducing from file", exc_info=True)
            if len(self.client.voice_clients) > 0:
                await self.client.voice_clients[0].disconnect()
            
    async def playWelcomeAudio(self, member, after, text_channel):
        try:
            f = open("users_audio_map.json", "r")
            user_ids_to_audio_map = json.loads(f.read())
            f.close()
            if not str(member.id) in user_ids_to_audio_map:
                return
            if not user_ids_to_audio_map[str(member.id)]["active"]:
                return
            if self.is_streaming:
                await text_channel.send(f"Estoy poniendo musiquita, no puedo saludarte {member.display_name}")
                return
            audio_files_list = user_ids_to_audio_map[str(member.id)]["audio_files"]
            random_idx = random.randint(0, len(audio_files_list) - 1)
            audio_file_name = audio_files_list[random_idx]
            if discord.opus.is_loaded():
                self.restartCounterIdleTimeout()
                if len(self.client.voice_clients) == 0:
                    await after.channel.connect()
                first_audio_source = discord.FFmpegPCMAudio(audio_file_name)
                if self.client.voice_clients[0].is_playing():
                    self.welcome_audios_queue.append(first_audio_source)
                    while True:
                        if not self.client.voice_clients[0].is_playing():
                            audio_source = self.welcome_audios_queue.pop()
                            self.client.voice_clients[0].play(audio_source)
                            if len(self.welcome_audios_queue) == 0:
                                break
                else:
                    self.client.voice_clients[0].play(first_audio_source)
                    await self.initCounterIdleTimeout()
        except Exception as e:
            if len(self.client.voice_clients) > 0:
                await self.client.voice_clients[0].disconnect()
            logging.error("While playing welcome audio", exc_info=True)
            
    async def playStreamingRadio(self, url, member, text_channel, max_failed_streaming_tries=MAX_FAILED_STREAMING_TRIES):
        try:
            vc = member.voice.channel
            if discord.opus.is_loaded():
                await text_channel.send("Cargando....")
                if len(self.client.voice_clients) == 0:
                    await vc.connect()
                if not self.client.voice_clients[0].is_playing():
                    streaming_thread = StreamingThread("Streaming Thread")
                    streaming_thread.setUrl(url)
                    streaming_thread.start()
                    await asyncio.sleep(7)
                    counter = 0
                    self.is_streaming = True
                    tries = 0
                    while self.is_streaming:
                        if not self.client.voice_clients[0].is_playing() :
                            if os.path.isfile(f"./assets/audio/streamings/{counter}.mp3"):
                                audio_source = discord.FFmpegPCMAudio(f"./assets/audio/streamings/{counter}.mp3")
                                self.client.voice_clients[0].play(audio_source)
                                counter += 1
                                tries = 0
                            else:
                                tries += 1
                                if tries == max_failed_streaming_tries:
                                    await text_channel.send("Abortando audio, algo salio mal")
                                    await self.stopStreaming()
                                    break
                                await asyncio.sleep(5)
                        await asyncio.sleep(0.0001)
                    streaming_thread.stop()
                    self._cleanupAudioFiles()
        except Exception as e:
            if len(self.client.voice_clients) > 0:
                await self.stopStreaming()
            logging.error("While streaming audio", exc_info=True)
            
    async def stopStreaming(self):
        if len(self.client.voice_clients) > 0:
            self.is_streaming = False
            self.client.voice_clients[0].stop()
            await self.disconnect()
            
    def _cleanupAudioFiles(self):
        deleter_thread = FileDeleterThread("RadioMp3Deleter", "./assets/audio/streamings", "^\w+\.mp3$")
        deleter_thread.start()
        
    async def disconnect(self):
        if len(self.client.voice_clients) > 0:
            if not self.client.voice_clients[0].is_playing() and self.client.voice_clients[0].is_connected():
                logging.warning(f"Disconnected from channel {self.client.voice_clients[0].channel}")
                await self.client.voice_clients[0].disconnect()
                
    def isVoiceClientPlaying(self):
        if len(self.client.voice_clients) > 0:
            return self.client.voice_clients[0].is_playing()
        
    def stopPlayer(self):
        if len(self.client.voice_clients) > 0:
            self.client.voice_clients[0].stop()
            
    def interruptStreaming(self):
        self.is_streaming = False
            
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
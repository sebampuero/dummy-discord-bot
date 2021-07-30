import logging
import asyncio
import random
from embeds.custom import VoiceEmbeds
from Utils.FileUtils import FileUtils
from Functionalities.Voice.VoiceSource import *
from Functionalities.Voice.VoiceQuery import *
from enum import Enum

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class State(object):

    """
    Abstract State base. Subclasses that inherit from this class represent any given voice state the bot is in. 
    """

    name = "state"

    def __init__(self, voice_manager, client):
        self.voice_manager = voice_manager
        self.client = client
        self.loop = client.loop
        self.song_loop = False
        self.current_volume = 1.0

    def switch(self, state):
        self.voice_manager.change_state(state)

    async def reproduce(self, query, **kwargs):
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
        asyncio.run_coroutine_threadsafe(self.voice_manager.disconnect(), self.client.loop)
        self._delete_music_cache()

    def _delete_music_cache(self):
        path = "./music_cache"
        pattern = r".*\..*"
        FileUtils.remove_files_in_dir(path, pattern)

    def __str__(self):
        return self.name 

class Off(State):

    name = "off"

    def __init__(self, voice_manager, client):
        super().__init__(voice_manager, client)

    async def reproduce(self, query, **kwargs):
        logger.warning("Unable to play because of state OFF")
        await self.voice_manager.disconnect()

    def switch(self, state):
        super(Off, self).switch(state)

class Radio(State):

    name = "radio"

    def __init__(self, voice_manager, client):
        super().__init__(voice_manager, client)
        self.current_volume = 0.1

    async def reproduce(self, query, **kwargs):
        try:
            self.voice_manager.voice_client.play(RadioSource(query, kwargs["radio_name"], volume=self.current_volume), after=lambda e: self.handle_error(e))
            self.voice_manager.current_player = self.voice_manager.voice_client._player
        except Exception as e:
            log = "while radio streaming"
            logger.error(log, exc_info=True)
            await self.voice_manager.current_context.send("Unexpected error")
            self.cleanup()

    def resume(self):
        if self.voice_manager.current_player:
            self.voice_manager.current_player.resume()
            self.voice_manager.voice_client._player = self.voice_manager.current_player

    def set_volume(self, volume):
        if self.voice_manager.current_player:
            self.voice_manager.current_player.source.volume = volume
            self.current_volume = volume

    def handle_error(self, error):
        if error:
            self.client.loop.create_task(self.voice_manager.current_context.send("An error occured"))
        self.cleanup()
            
    def switch(self, state):
        self.voice_manager.pause_player()
        super(Radio, self).switch(state)
    

class Stream(State):

    name = "stream"
    MAX_YDL_FAILED_ATTEMPTS = 4

    class Effect(Enum):

        EQUALIZER = 1
        BASS = 2
        METAL = 3
        VAPORWAVE = 4
        EAR_RAPE = 5
        CHORUS = 6
        VIBRATO = 7
        EIGHTM_SIM = 8
        SUPEREQUALIZER = 9
        SLOW_DOWN = 10
        SPEED_UP = 11


    def __init__(self, voice_manager, client):
        super().__init__(voice_manager, client)
        self.queue = []
        self.last_query = None
        self.is_downloading = False
        self.current_volume = 0.1
        self.failed_youtube_dl_attempts = 0
        self.ffmpeg_options = {}
    
    async def reproduce(self, query, **kwargs):
        self.original_msg = kwargs["original_msg"]
        self.queue.extend(query) if isinstance(query, list) else self.queue.insert(0, query)
        if not self.voice_manager.is_voice_client_playing() and not self.is_downloading:
            await self.music_loop(error=None)

    async def seek_to(self, second, ffmpeg_options=None):
        self.voice_manager.interrupt_player()
        self.ffmpeg_options = {'before_options': f"-ss {second}"}
        if ffmpeg_options:
            self.ffmpeg_options.update(ffmpeg_options)
        self.queue.append(self.last_query)
        await self.music_loop(error=None)
        self._update_song_progress(second)

    def song_progress(self):
        if self.voice_manager.current_player:
            return self.voice_manager.current_player.source.get_progress_seconds()

    async def restore_effects(self):
        current_secods = self.voice_manager.current_player.source.get_progress_seconds()
        await self.seek_to(current_secods)

    async def test_effect_ffmpeg(self, ffmpeg_filter):
        ffmpeg_options = {'options': f'-af "{ffmpeg_filter}"'}
        await self._apply_ffmpeg_options(ffmpeg_options)

    async def apply_effect_ffmpeg(self, effect_type):
        if effect_type == Stream.Effect.EQUALIZER:
            await self.test_effect_ffmpeg("equalizer=f=440:width_type=o:width=2:g=12.0")
        elif effect_type == Stream.Effect.VIBRATO:
            await self.test_effect_ffmpeg("aphaser=type=t:speed=2:decay=0.6")
        elif effect_type == Stream.Effect.BASS:
            await self.test_effect_ffmpeg("bass=g=12.0")
        elif effect_type == Stream.Effect.CHORUS:
            await self.test_effect_ffmpeg("chorus=0.5:0.9:50|60|70:0.3|0.22|0.3:0.25|0.4|0.3:2|2.3|1.3")
        elif effect_type == Stream.Effect.EAR_RAPE:
            await self.test_effect_ffmpeg("acrusher=level_in=8:level_out=18:bits=8:mode=log:aa=1")
        elif effect_type == Stream.Effect.EIGHTM_SIM:
            await self.test_effect_ffmpeg("apulsator=hz=0.125")
        elif effect_type == Stream.Effect.VAPORWAVE:
            await self.test_effect_ffmpeg("vibrato=f=5,bass=g=10.0")
        elif effect_type == Stream.Effect.METAL:
            await self.test_effect_ffmpeg("aecho=0.8:0.88:8:0.8")
        elif effect_type == Stream.Effect.SUPEREQUALIZER:
            await self.test_effect_ffmpeg("superequalizer=1b=10:2b=10:3b=1:4b=5:5b=7:6b=5:7b=2:8b=3:9b=4:10b=5:11b=6:12b=7:13b=8:14b=8:15b=9:16b=9:17b=10:18b=10[a];[a]loudnorm=I=-16:TP=-1.5:LRA=14")
        elif effect_type == Stream.Effect.SLOW_DOWN:
            await self.test_effect_ffmpeg("atempo=0.5")
        elif effect_type == Stream.Effect.SPEED_UP:
            await self.test_effect_ffmpeg("atempo=2.0")

    async def _apply_ffmpeg_options(self, options):
        current_secods = self.voice_manager.current_player.source.get_progress_seconds()
        await self.seek_to(current_secods, ffmpeg_options=options)

    def _update_song_progress(self, seconds):
        if self.voice_manager.current_player:
            self.voice_manager.current_player.source.set_progress_ms(seconds)

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
            self.edit_msg()

    def retrieve_query_for_source(self):
        if self.song_loop:
            return self.last_query
        return self.queue.pop()

    def format_embed(self):
        data = {
                'title': f'Playing {self.voice_manager.voice_client.source.title}',
                'url': self.voice_manager.voice_client.source.url,
                'author': {
                    "name": self.voice_manager.current_context.author.display_name
                },
                'fields': [
                    {
                        "name": "Duration",
                        "value": str(self.voice_manager.voice_client.source.duration),
                        "inline": False
                    },
                    {
                        "name": "Songs",
                        "value": str(len(self.queue)),
                        "inline": False
                    },
                    {
                        "name": "Volume",
                        "value": str(self.current_volume * 100) + "%",
                        "inline": True
                    }
                ]

            }
        if len(self.queue) > 0:
            data["fields"].append({
                "name": "Next song: ",
                "value": str(self.queue[len(self.queue) - 1]),
                "inline": False
            })
        return VoiceEmbeds.from_dict(data)

    def edit_msg(self):
        asyncio.run_coroutine_threadsafe(self.original_msg.edit(embed=self.format_embed()), self.client.loop)

    async def next_interim_msg(self):
        msg = await self.voice_manager.current_context.send("About to play next song...")
        self.original_msg = msg

    def playback_finished(self, error):
        self.loop.create_task(self.music_loop(error=None))

    async def music_loop(self, error):
        if error:
            return self.cleanup()
        if len(self.queue) == 0 and not self.song_loop:
            await self.voice_manager.current_context.send("End of playing list")
            return self.cleanup()
        query = self.retrieve_query_for_source()
        self.last_query = query
        try:
            self.is_downloading = True
            if isinstance(query, SoundcloudQuery):
                source = await SoundcloudSource.from_query(self.loop, query, self.current_volume, **self.ffmpeg_options)
            elif isinstance(query, LocalMP3Query):
                source = MP3FileSource(query, self.current_volume, **self.ffmpeg_options)
            else:
                source = await YTDLSource.from_query(self.loop, query, self.current_volume, **self.ffmpeg_options)
            self.is_downloading = False
            self.voice_manager.voice_client.play(source, after=lambda e: self.playback_finished(e))
            self.voice_manager.current_player = self.voice_manager.voice_client._player
            self.edit_msg()
            self.failed_youtube_dl_attempts = 0
        except discord.ClientException as e:
            logger.error("while streaming", exc_info=True)
            await self.voice_manager.current_context.send("Unexpected error")
            self.cleanup()
        except CustomClientException as e:
            logger.error("custom client exc", exc_info=True)
            await self.voice_manager.current_context.send(str(e), delete_after=10.0)
            await self.music_loop(error=None)
            self.is_downloading = False
        except Exception as e:
            if self.failed_youtube_dl_attempts < Stream.MAX_YDL_FAILED_ATTEMPTS:
                logger.info(f"Retrying after error {str(e)}")        
                self.failed_youtube_dl_attempts += 1
                self.queue.append(self.last_query)
                await asyncio.sleep(0.1)
                return await self.music_loop(error=None)
            error_msg = "An error occurred playing current song, trying to play the next song in the list"
            await self.voice_manager.current_context.send(error_msg, delete_after=5.0)
            await self.music_loop(error=None)
            logger.error("while streaming, skipping to next song", exc_info=True)        
            self.failed_youtube_dl_attempts = 0
            self.is_downloading = False
        else:
            self.ffmpeg_options.clear()

    def cleanup(self):        
        self.queue.clear()
        self.song_loop = False
        self.is_downloading = False
        self.failed_youtube_dl_attempts = 0
        try: 
            logger.info("Cleaning up source")
            self.voice_manager.current_player.source.cleanup()
        except:
            pass
        super(Stream, self).cleanup()

class Speak(State):

    name = "speak"

    def __init__(self, voice_manager, client):
        super().__init__(voice_manager, client)

    async def reproduce(self, url, **kwargs):
        voice_client = self.voice_manager.voice_client
        try:
            if isinstance(self.voice_manager.prev_state, Off):
                voice_client.play(StreamSource(discord.FFmpegPCMAudio(url), url, self.current_volume), after= lambda e: self.cleanup())
            else:
                voice_client.play(StreamSource(discord.FFmpegPCMAudio(url), url, self.current_volume), after= lambda e: self.resume_playing_for_prev_state(e))
        except Exception as e:
            log = "while speaking"
            logger.error(log, exc_info=True)
            await self.voice_manager.current_context.send("Unexpected error")
            self.cleanup()

    def resume_playing_for_prev_state(self, error):
        if error:
            return self.switch(self.voice_manager.off)
        self.switch(self.voice_manager.prev_state)
        self.voice_manager.resume_previous()

class Salute(State):

    name = "salute"

    def __init__(self, voice_manager, client):
        super().__init__(voice_manager, client)
        self.welcome_audios_queue = []

    async def reproduce(self, query, **kwargs):
        self.welcome_audios_queue.append(LocalfileSource(query))
        if not self.voice_manager.is_voice_client_playing():
            self.salute_loop(error=None)
        
    def salute_loop(self, error):
        if error:
            return self.cleanup()
        if len(self.welcome_audios_queue) == 0:
            if isinstance(self.voice_manager.prev_state, Off):
                return self.cleanup()
            else:
                return self.resume_playing_for_prev_state(error)
        source = self.welcome_audios_queue.pop()
        try:
            self.voice_manager.voice_client.play(source, after=lambda e: self.salute_loop(e))
        except Exception as e:
            log = "while welcoming audio"
            logger.error(log, exc_info=True)
            self.cleanup()

    def resume_playing_for_prev_state(self, error):
        if error:
            return self.cleanup()
        self.switch(self.voice_manager.prev_state)
        self.voice_manager.resume_previous()
import logging
import asyncio
import random
from embeds.custom import VoiceEmbeds
from Utils.FileUtils import FileUtils
from Utils.LoggerSaver import *
from Functionalities.Voice.VoiceSource import *
from Functionalities.Voice.VoiceQuery import *

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
        asyncio.run_coroutine_threadsafe(self.voice_manager.disconnect(), self.client.loop)

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
        self.current_volume = 0.3

    def reproduce(self, query, **kwargs):
        try:
            self.voice_manager.voice_client.play(RadioSource(query, kwargs["radio_name"], volume=self.current_volume), after=lambda e: self.handle_error(e))
            self.voice_manager.current_player = self.voice_manager.voice_client._player
        except Exception as e:
            log = "while radio streaming"
            logging.error(log, exc_info=True)
            LoggerSaver.save_log(f"{log} {str(e)}", WhatsappLogger())
            asyncio.run_coroutine_threadsafe(self.voice_manager.current_context.send("Error inesperado"), self.client.loop)
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
            self.client.loop.create_task(self.voice_manager.current_context.send("Se produjo un error"))
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
        if self.voice_manager.voice_client and isinstance(self.voice_manager.voice_client.source, YTDLSource):
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
            return self.cleanup()
        if len(self.queue) == 0 and not self.trigger_loop:
            asyncio.run_coroutine_threadsafe(self.voice_manager.current_context.send("Fin de la lista de reproduccion"), self.client.loop)
            return self.cleanup()
        if self.voice_manager.voice_client.source:
            self.remove_video_file()
        query = self.retrieve_query_for_source()
        self.last_query = query
        try:
            source = SoundcloudSource.from_query(query.the_query, self.current_volume) if isinstance(query, SoundcloudQuery) else \
                YTDLSource.from_query(query.the_query, self.current_volume)
            self.voice_manager.voice_client.play(source, after=lambda e: self.music_loop(e))
            self.voice_manager.current_player = self.voice_manager.voice_client._player
            self.edit_msg()
        except discord.ClientException as e:
            log = "while streaming"
            logging.error(log, exc_info=True)
            LoggerSaver.save_log(f"{log} {str(e)}", WhatsappLogger())
            asyncio.run_coroutine_threadsafe(self.voice_manager.current_context.send("Error inesperado"), self.client.loop)
            self.cleanup()
        except CustomClientException as e:
            asyncio.run_coroutine_threadsafe(self.voice_manager.current_context.send(str(e)), self.client.loop)
            LoggerSaver.save_log(str(e), WhatsappLogger())
            self.cleanup()
        except Exception as e:
            error_msg = "Se produjo un error reproduciendo cancion actual, intentando reproducir siguiente canción en lista"
            asyncio.run_coroutine_threadsafe(self.voice_manager.current_context.send(error_msg), self.client.loop)
            self.music_loop(error=None)
            log = "while streaming, skipping to next song"
            logging.error(log, exc_info=True)
            LoggerSaver.save_log(f"{log} {str(e)}", WhatsappLogger())

    def cleanup(self):        
        #self.voice_manager.pause_player()
        self.remove_video_file()
        self.queue = []
        self.trigger_loop = False
        self.shuffle_for_queue = False
        super(Stream, self).cleanup()


class Speak(State):

    name = "speak"

    def __init__(self, voice_manager, client):
        super().__init__(voice_manager, client)

    def reproduce(self, url, **kwargs):
        voice_client = self.voice_manager.voice_client
        try:
            if isinstance(self.voice_manager.prev_state, Off):
                voice_client.play(StreamSource(discord.FFmpegPCMAudio(url), url), after= lambda e: self.cleanup())
            else:
                voice_client.play(StreamSource(discord.FFmpegPCMAudio(url), url), after= lambda e: self.resume_playing_for_prev_state(e))
        except Exception as e:
            log = "while speaking"
            logging.error(log, exc_info=True)
            LoggerSaver.save_log(f"{log} {str(e)}", WhatsappLogger())
            asyncio.run_coroutine_threadsafe(self.voice_manager.current_context.send("Error inesperado"), self.client.loop)
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

    def reproduce(self, query, **kwargs):
        voice_client = self.voice_manager.voice_client
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
                self.switch(self.voice_manager.prev_state)
                return self.resume_playing_for_prev_state(error)
        source = self.welcome_audios_queue.pop()
        try:
            self.voice_manager.voice_client.play(source, after=lambda e: self.salute_loop(e))
        except Exception as e:
            log = "while welcoming audio"
            logging.error(log, exc_info=True)
            LoggerSaver.save_log(f"{log} {str(e)}", WhatsappLogger())
            self.cleanup()

    def resume_playing_for_prev_state(self, error):
        if error:
            return self.cleanup()
        self.switch(self.voice_manager.prev_state)
        self.voice_manager.resume_previous()
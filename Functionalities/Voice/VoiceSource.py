import discord
import logging
from youtube_dl import YoutubeDL
from Utils.LoggerSaver import *
from exceptions.CustomException import CustomClientException
from requests import exceptions
from Utils.TimeUtils import TimeUtils
import requests
import soundcloud
import os

with open("./config/creds.json", "r") as f:
    creds = json.loads(f.read())
    soundcloud_client = soundcloud.Client(client_id=creds["soundcloud"])

class LocalfileSource(discord.PCMVolumeTransformer):
    
    def __init__(self, file_name, options=None, before_options=None):
        super().__init__(discord.FFmpegPCMAudio(file_name, options=options, before_options=before_options), volume=1.0)

        self.file_name = file_name

class StreamSource(discord.PCMVolumeTransformer):

    def __init__(self, source,url, volume=1.0):
        super().__init__(source, volume)
        self.url = url
        self.duration = 0
        self.progress = 0

    ffmpeg_options = {
        'options': '',
        'before_options': ''
    }

    @classmethod
    def clear_ffmpeg_options(cls):
        cls.ffmpeg_options['options'] = ''
        cls.ffmpeg_options['before_options'] = ''

    def get_progress_seconds(self):
        return int(self.progress * 20 / 1000) # returns progress in seconds

    def set_progress_ms(self, seconds):
        self.progress = int(seconds * 1000 / 20)

    @staticmethod
    def parse_duration(duration: int):
        return TimeUtils.parse_seconds(duration)

    def read(self):
        self.progress = self.progress + 1 # every progress step is worth 20ms
        return super().read()

class MP3FileSource(StreamSource):

    def __init__(self, url, title, volume=0.3, options=None, before_options=None):
        super().__init__(discord.FFmpegPCMAudio(url, options=options, before_options=before_options), url, volume=volume)
        self.title = title

class RadioSource(StreamSource):

    def __init__(self, url, radio_name, volume=0.3, options=None, before_options=None):
        super().__init__(discord.FFmpegPCMAudio(url, options=options, before_options=before_options), url, volume=0.3)
        self.name = radio_name

class SoundcloudSource(StreamSource):

    def __init__(self, url, volume, track, options=None, before_options=None):
        super().__init__(discord.FFmpegPCMAudio(url, options=options, before_options=before_options), url, volume)
        self.title = track.title
        self.duration = self.parse_duration(int(track.full_duration / 1000))
        self.url = track.uri

    @classmethod
    def from_query(cls, query, volume=0.3, options=None, before_options=None):
        try:
            cls.clear_ffmpeg_options()
            if options:
                cls.ffmpeg_options['options'] += options
            if before_options:
                cls.ffmpeg_options['before_options'] += before_options
            the_track = soundcloud_client.get("resolve", url=query)
            track = soundcloud_client.get(f"tracks/{the_track.id}")
            if not track.streamable or track.kind != "track":
                raise CustomClientException("Track no valida")
            stream = None
            for transcoding in track.media["transcodings"]:
                if transcoding["format"]["protocol"] == "progressive":
                    stream = soundcloud_client.get(transcoding["url"], allow_redirects=True)
            if stream:
                obj = requests.get(stream.url)
                return cls(json.loads(obj.text)["url"], volume, track, **cls.ffmpeg_options)
            else:
                raise CustomClientException("Track no es streameable")
        except exceptions.HTTPError as e:
            LoggerSaver.save_log(str(e), WhatsappLogger())
            raise CustomClientException("Link posiblemente mal formateado")
        except Exception as e:
            raise CustomClientException(str(e))

class YTDLSource(StreamSource):
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

    def __init__(self, source, data, volume=0.3):
        super().__init__(source, data.get('filename_vid'), volume)
        self.title = data.get('title', '')
        self.duration = self.parse_duration(int(data.get('duration', 0)))
        self.url = data.get('webpage_url', '')
        self.filename = data.get('filename_vid', '')

    @classmethod
    def from_query(cls, query, volume=0.3, options=None, before_options=None):
        cls.clear_ffmpeg_options()
        if options:
            cls.ffmpeg_options['options'] += options
        cls.ffmpeg_options['options'] += " -vn"
        if before_options:
            cls.ffmpeg_options['before_options'] += before_options
        logging.warning(f"Using options {cls.ffmpeg_options}")
        query = " ".join(query) if not isinstance(query, str) else query
        with YoutubeDL(YTDLSource.ytdl_opts) as ydl:
            info = ydl.extract_info(query, download=False)
            if 'entries' in info:  # grab the first video
                info = info['entries'][0]
            path = ydl.prepare_filename(info)
            if os.path.isfile(path):
                data = info
                data["filename_vid"] = path
                return cls(discord.FFmpegPCMAudio(path, **cls.ffmpeg_options), data, volume)
            if not info['is_live']:
                data = ydl.extract_info(query)  # TODO run in executor?
            else:
                #TODO parse the live video anyways
                raise CustomClientException("No hay soporte para live videos aun")

            if 'entries' in data:  # if we get a playlist, grab the first video TODO does ytdl_opts['noplaylist'] prevent this error?
                data = data['entries'][0]
            path = ydl.prepare_filename(data)
            data["filename_vid"] = path
            return cls(discord.FFmpegPCMAudio(path, **cls.ffmpeg_options), data, volume)
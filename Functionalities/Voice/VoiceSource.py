import discord
import logging
from youtube_dl import YoutubeDL
import youtube_dl
from Utils.LoggerSaver import *
from exceptions.CustomException import CustomClientException
from Utils.TimeUtils import TimeUtils
import aiohttp
import soundcloud
import functools
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

with open("./config/creds.json", "r") as f:
    creds = json.loads(f.read())
    soundcloud_client = soundcloud.Client(client_id=creds["soundcloud"])

class LocalfileSource(discord.PCMVolumeTransformer):
    
    def __init__(self, file_name, options=None, before_options=None):
        super().__init__(discord.FFmpegPCMAudio(file_name, options=options, before_options=before_options), volume=1.0)

        self.file_name = file_name

class StreamSource(discord.PCMVolumeTransformer):

    def __init__(self, source,url, volume):
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

    def __init__(self, query, volume, options=None, before_options=None):
        url = query.the_query
        super().__init__(discord.FFmpegPCMAudio(url, options=options, before_options=before_options), url, volume=volume)
        self.title = query.title

class RadioSource(StreamSource):

    def __init__(self, url, radio_name, volume, options=None, before_options=None):
        super().__init__(discord.FFmpegPCMAudio(url, options=options, before_options=before_options), url, volume=0.3)
        self.name = radio_name

class SoundcloudSource(StreamSource):

    def __init__(self, url, volume, track, options=None, before_options=None):
        super().__init__(discord.FFmpegPCMAudio(url, options=options, before_options=before_options), url, volume)
        self.title = track.title
        self.duration = self.parse_duration(int(track.full_duration / 1000))
        self.url = track.uri

    @classmethod
    async def from_query(cls, loop, query, volume, options=None, before_options=None):
        url = query.the_query
        cls.clear_ffmpeg_options()
        if options:
            cls.ffmpeg_options['options'] += options
        if before_options:
            cls.ffmpeg_options['before_options'] += before_options
        the_track = soundcloud_client.get("resolve", url=url)
        track = soundcloud_client.get(f"tracks/{the_track.id}")
        if not track.streamable or track.kind != "track":
            raise CustomClientException("Invalid track")
        stream = None
        for transcoding in track.media["transcodings"]:
            if transcoding["format"]["protocol"] == "progressive":
                stream = soundcloud_client.get(transcoding["url"], allow_redirects=True)
        if stream:
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(stream.url) as obj:
                        streaming_content = await obj.text() 
                        return cls(json.loads(streaming_content)["url"], volume, track, **cls.ffmpeg_options)
                except aiohttp.ClientConnectionError as e:
                    logger.error(str(e), exc_info=True)
                    raise CustomClientException("Link possibly badly formatted, track info could not be obtained")
        else:
            raise CustomClientException("Track is not streameable")

def hook(d):
    if d['status'] == 'error':
        logger.info("Error ocurred")
    if d['status'] == 'finished':
        logger.info(f"Done with {d['filename']}")
    if d['status'] == 'downloading':
        p = d['_percent_str']
        p = p.replace('%','')
        logger.info(f"{d['filename']}, {d['_percent_str']}, ETA {d['_eta_str']}")

class YTDLSource(StreamSource):
    ytdl_opts = {
        'match_filter': youtube_dl.utils.match_filter_func("!is_live"),
        'quiet': True,
        'format': 'bestaudio/best',
        'noplaylist': True,
        'cookiefile': 'cookies.txt',
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'outtmpl': './music_cache/%(extractor)s-%(title)s.%(ext)s',
        'restrictfilenames': True,
        #'simulate': True,
        'nooverwrites': True,
        #'skip_download': False,
        'logtostderr': False,
        'no_warnings': True,
        'socket_timeout': 5,
        #'progress_hooks': [hook],
        'default_search': 'auto',
        'source_address': '0.0.0.0'
    }

    def __init__(self, source, data, volume):
        super().__init__(source, data.get('filename_vid'), volume)
        self.title = data.get('title', '')
        self.duration = self.parse_duration(int(data.get('duration', 0)))
        self.url = data.get('webpage_url', '')
        self.filename = data.get('filename_vid', '')

    @classmethod
    async def from_query(cls, loop, youtube_query, volume, options=None, before_options=None):
        cls.clear_ffmpeg_options()
        if options:
            cls.ffmpeg_options['options'] += options
        cls.ffmpeg_options['options'] += " -vn"
        if before_options:
            cls.ffmpeg_options['before_options'] += before_options
        search_query = " ".join(youtube_query.the_query) if isinstance(youtube_query.the_query, tuple) else youtube_query.the_query
        if youtube_query.data:
            return cls(discord.FFmpegPCMAudio(youtube_query.data["filename_vid"], **cls.ffmpeg_options), youtube_query.data, volume)
        with YoutubeDL(YTDLSource.ytdl_opts) as ydl:
            data = await cls.download_data(loop, ydl, url=search_query)
            if 'entries' in data: 
                data = data['entries'][0]
            if data['is_live']:
                raise CustomClientException("I do not support live videos, send the link of the specific video")
            path = ydl.prepare_filename(data)
            data["filename_vid"] = path
            youtube_query.set_data(data)
            return cls(discord.FFmpegPCMAudio(path, **cls.ffmpeg_options), data, volume)

    @classmethod
    async def download_data(cls, loop, ydl, *args, **kwargs):
        thread_pool = ThreadPoolExecutor(max_workers=2)
        return await loop.run_in_executor(thread_pool, functools.partial(ydl.extract_info, *args, **kwargs))
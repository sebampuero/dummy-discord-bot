import discord
import requests
import io

r = requests.get("http://s1.vvtelecom.net:8000/kebuenaptv?listening-from-radio-garden", stream=True)
for data in r.iter_content(2048):
    discord.FFmpegPCMAudio(io.StringIO("Hello hello hello"), pipe=True)
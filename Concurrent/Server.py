from flask import Flask, request, Response, render_template
from Concurrent.OurThread import OurThread
from Utils.NetworkUtils import NetworkUtils
from Routes.BotBlueprint import get_bot_blueprint
import asyncio
#from Routes.Main import main_routes

class Server(OurThread):
    
    def __init__(self, name):
        super(Server, self).__init__()
        self.name = name
        self.loop = asyncio.get_event_loop()
        print(f"Init {self.name} thread")
    
    def setVoice(self, voice):
        self.voice = voice
    
    def setGuild(self, guild):
        self.guild = guild
        
    def setChatChannel(self, text_channel):
        self.text_channel = text_channel
    
    def run(self):
        app = Flask(__name__, template_folder='../templates/')
        app.register_blueprint(get_bot_blueprint(self.guild, self.voice, self.text_channel, self.loop), url_prefix="/")  
        app.run(host="0.0.0.0", port=80, debug=True, use_reloader=False)
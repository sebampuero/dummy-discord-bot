from flask import Flask, request, Response
from Concurrent.OurThread import OurThread
from Utils.NetworkUtils import NetworkUtils
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
    
    def run(self):
        app = Flask(__name__)
        
        guild = self.guild
        voice = self.voice
        
        async def say(data, guild, voice):
            text = str(data["text"]).lower()
            member_name = str(data["member_name"]).lower()
            for member in guild.members:
                if member_name in str(member.display_name.lower()):
                    network_utils = NetworkUtils()
                    audio_filename = await network_utils.getAndSaveTtsLoquendoVoice(text)
                    await voice.reproduceFromFile(member, audio_filename)
        
        @app.route("/", methods=["POST"])
        def transmit():
            try:
                data = request.json
                self.loop.create_task(say(data, guild, voice))
                return Response("{'message': 'OK'}", status=200, mimetype='application/json')
            except Exception as e:
                print(str(e))
    
        app.run(host="0.0.0.0", debug=True, use_reloader=False)
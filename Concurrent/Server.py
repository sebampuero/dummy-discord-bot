from flask import Flask, request, Response, render_template
from Concurrent.OurThread import OurThread
from Routes.BotBlueprint import get_bot_blueprint
import asyncio

class Server(OurThread):
    
    def __init__(self, name):
        super(Server, self).__init__()
        self.name = name
        self.loop = asyncio.get_event_loop()
        self.daemon = True
        print(f"Init {self.name} thread")
    
    def set_voice(self, voice):
        self.voice = voice
    
    def set_client(self, client):
        self.client = client
    
    def run(self):
        app = Flask(__name__, template_folder='../templates/')
        app.register_blueprint(get_bot_blueprint(self.client, self.voice, self.loop), url_prefix="/")  
        app.run(host="0.0.0.0", port=80, debug=True, use_reloader=False) #TODO: change api endpoint port to 3000 and let nginx handle static data
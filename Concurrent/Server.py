from flask import Flask, request, Response, render_template
from Routes.BotBlueprint import get_bot_blueprint
import asyncio
import threading

class Server(threading.Thread):
    
    def __init__(self, name, client):
        super().__init__()
        self.name = name
        self.daemon = True
        self.client = client
        print(f"Init {self.name} thread")
    
    def run(self):
        app = Flask(__name__, template_folder='../templates/')
        app.register_blueprint(get_bot_blueprint(self.client), url_prefix="/bot")  
        app.run(host="127.0.0.1", port=3000, debug=True, use_reloader=False) #TODO: change api endpoint port to 3000 and let nginx handle static data
from flask import Blueprint

class MainRoutes():
    
    main_routes = Blueprint('main', __name__)
    
    def __init__(self, discord_client, voice):
        self.client = discord_client
        self.voice = voice

    @main_routes.route("/", methods=['GET'])
    def main():
        return "Hello"
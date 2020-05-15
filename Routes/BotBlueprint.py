from flask import Blueprint, request, Response, render_template
from Utils.NetworkUtils import NetworkUtils

async def say(data, guild, voice):
    text = str(data["text"]).lower()
    member_name = str(data["select_name"]).lower()
    loquendo_voice = str(data["voice"])
    for member in guild.members:
        if member_name in str(member.display_name.lower()) and member.voice != None:
            network_utils = NetworkUtils()
            audio_filename = await network_utils.getAndSaveTtsLoquendoVoice(text, voice=loquendo_voice)
            await voice.reproduceFromFile(member, audio_filename)

def get_bot_blueprint(guild, voice, event_loop):
    
    bot_blueprint = Blueprint("bot", __name__)
    
    @bot_blueprint.route("/", methods=["POST", "GET"])
    def transmit():
        if request.method == "POST":
            try:
                data = request.json
                event_loop.create_task(say(data, guild, voice))
                return Response("{'message': 'OK'}", status=200, mimetype='application/json')
            except Exception as e:
                print(str(e))
                Response("{'message': 'ERROR'}", status=500, mimetype='application/json')
        members_list_with_voice = []
        for member in guild.members:
            if member.voice != None and not member.bot:
                members_list_with_voice.append(member.display_name)
        return render_template("index.html", members=members_list_with_voice)
    
    return bot_blueprint
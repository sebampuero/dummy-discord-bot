from flask import Blueprint, request, jsonify, render_template
from Utils.NetworkUtils import NetworkUtils
import Constants.StringConstants as Constants

async def say(data, guild, text_channel, voice):
    text = str(data["text"]).lower()
    member_name = str(data["select_name"]).lower()
    loquendo_voice = str(data["voice"])
    for member in guild.members:
        if member_name in str(member.display_name.lower()) and member.voice != None:
            network_utils = NetworkUtils()
            audio_filename = await network_utils.getAndSaveTtsLoquendoVoice(text, voice=loquendo_voice)
            if audio_filename != "":
                await voice.reproduceFromFile(member, audio_filename)
            else:
                await text_channel.send(f"No se pudo reproducir '{text}', seguramente se fue a la mierda la pagina de loquendo")

async def sendDm(data, guild):
    text = str(data["text"]).strip()
    member_name = str(data["to"]).lower().strip()
    for member in guild.members:
        if member_name in str(member.display_name.lower()):
            dm_channel = await member.create_dm()
            await dm_channel.send(text)
    
def get_bot_blueprint(guild, voice, text_channel, event_loop):
    
    bot_blueprint = Blueprint("bot", __name__)
    
    @bot_blueprint.route("/")
    def index():
        members_list_with_voice = []
        for member in guild.members:
            if member.voice != None and not member.bot:
                members_list_with_voice.append(member.display_name)
        return render_template("index.html", members=members_list_with_voice)
    
    @bot_blueprint.route("/say", methods=["POST"])
    def reproduceFromText():
        try:
            if voice.isVoiceClientPlaying():
                return jsonify({'message': Constants.BOT_BUSY_RESPONSE}), 200
            data = request.json
            event_loop.create_task(say(data, guild, text_channel, voice))
            return jsonify({'message': Constants.TRYING_REPR_AUDIO}), 201
        except Exception as e:
            print(str(e))
            return jsonify({'message': Constants.THERE_WAS_AN_ERROR}), 500
        
    @bot_blueprint.route("/dm", methods=["POST"])
    def privateMessage():
        try:
            data = request.json
            event_loop.create_task(sendDm(data, guild))
            return jsonify({'message': 'OK'}), 201
        except Exception as e:
            print(str(e))
            return jsonify({'message': Constants.THERE_WAS_AN_ERROR}), 500
    return bot_blueprint
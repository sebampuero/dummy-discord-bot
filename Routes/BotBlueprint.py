from flask import Blueprint, request, jsonify, render_template
from Utils.NetworkUtils import NetworkUtils
import Constants.StringConstants as Constants
from BE.BotBE import BotBE
from types import SimpleNamespace
from Voice import Speak, Salute

async def say(data, guild, text_channel, voice):
    text = str(data["text"]).lower()
    member_name = str(data["select_name"]).lower()
    loquendo_voice = str(data["voice"])
    for member in guild.members:
        if member_name in str(member.display_name.lower()) and member.voice != None:
            network_utils = NetworkUtils()
            audio_filename = await network_utils.get_loquendo_voice(text, voice=loquendo_voice)
            if audio_filename != "":
                await voice.reproduce_from_file(member, audio_filename)
            else:
                await text_channel.send(f"No se pudo reproducir '{text}', seguramente se fue a la mierda la pagina de loquendo")
    
def get_bot_blueprint(client, voice, event_loop):
    
    guild = client.get_guild(451813158290587649)
    text_channel = client.get_channel(451813158747635723)

    bot_blueprint = Blueprint("bot", __name__)
    
    @bot_blueprint.route("/members")
    def get_members():
        members_list_with_voice = []
        for member in guild.members:
            if member.voice != None and not member.bot:
                members_list_with_voice.append(member.display_name)
        return jsonify({"members": members_list_with_voice})
    
    @bot_blueprint.route("/say", methods=["POST"])
    def reproduce_from_text():
        try:
            playing_state = voice.get_playing_state(SimpleNamespace(guild=guild))
            if isinstance(playing_state, Speak) or isinstance(playing_state, Salute):
                return jsonify({'message': Constants.BOT_BUSY_RESPONSE}), 200
            data = request.json
            event_loop.create_task(say(data, guild, text_channel, voice))
            return jsonify({'message': Constants.TRYING_REPR_AUDIO}), 201
        except Exception as e:
            print(str(e))
            return jsonify({'message': Constants.THERE_WAS_AN_ERROR}), 500
    return bot_blueprint
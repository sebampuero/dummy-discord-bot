from flask import Blueprint, request, jsonify, render_template
from Utils.NetworkUtils import NetworkUtils
import Constants.StringConstants as Constants
from BE.BotBE import BotBE
from types import SimpleNamespace
from Voice import Speak, Salute
from gtts import gTTS

async def say(data, guild, text_channel, voice):
    text = str(data["text"]).lower()
    member_name = str(data["select_name"]).lower()
    language = str(data["language"])
    for member in guild.members:
        if member_name in str(member.display_name.lower()) and member.voice != None:
            network_utils = NetworkUtils()
            tts_es = gTTS(text, lang=language)
            url = tts_es.get_urls()[0]
            status, content_type = await network_utils.website_check(url)
            if status == 200:
                await voice.reproduce_from_file(member, url)
            else:
                await text_channel.send(f"No se pudo reproducir '{text}'")
    
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
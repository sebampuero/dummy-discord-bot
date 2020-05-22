import random
from Utils.NetworkUtils import NetworkUtils
import Constants.StringConstants as Constants
import json
"""
MessageProcessor is responsible for processing all incoming (relevant) messages from a Discord text channel
"""

class MessageProcessor():
    
    def __init__(self, voice, subscription, quote, alert, server_manager):
        self.voice = voice
        self.subscription = subscription
        self.quote = quote
        self.alert = alert
        self.server_manager = server_manager
        
    async def handleAllMessages(self, message, text_channel):
        the_message = message.content.lower()
        if the_message.startswith("-subscribe"):
            await self.subscription.handleSubscribe(message, text_channel)
        elif the_message.startswith("-unsubscribe"):
            await self.subscription.handleUnsubscribe(message, text_channel)
        elif the_message.startswith("-dailyquote"):
            await self.quote.handleQuoteSave(message, text_channel)
        elif the_message.startswith("-set-alert"):
            await self.alert.handleAlertSet(message, text_channel)
        elif the_message.startswith("-unset-alert"):
            await self.alert.handleUnsetAlert(message, text_channel)
        elif the_message.startswith("--help"):
            await self.formatHelpMessage(text_channel)
        elif the_message.startswith("-audio-off"):
            await self.voice.deactivateWelcomeAudio(message, text_channel)
        elif the_message.startswith("-audio-on"):
            await self.voice.activateWelcomeAudio(message, text_channel)
        elif the_message.startswith("-say"):
            await self.handleTextToVoiceTranslation(message, text_channel)
        elif the_message.startswith("-show-radios"):
            await self.handleShowRadios(text_channel)
        elif the_message.startswith("-start-radio"):
            await self.handleStreamingRadio(message, text_channel)
        elif the_message.startswith("-change-radio"):
            await self.handleChangeRadio(message, text_channel)
        elif the_message.startswith("-stop-radio"):
            await self.handleStopStreamingRadio(message, text_channel)
        else:
            await self.handleCustomMessages(message, text_channel)
            
    async def handleShowRadios(self, text_channel):
        f = open("radio_stations.json", "r")
        radios = json.loads(f.read())
        f.close()
        msg = ""
        for key, value in radios.items():
            msg = msg + "Ciudad: " + str(key) + "\n"
            loop = 0
            for radio in value["items"]:
                loop += 1
                msg = msg + f"{loop} " + radio["name"] + "\n"
        await text_channel.send(msg)
            
            
    async def _isUserInVoiceChannel(self, voice_state, text_channel):
        if voice_state == None:
            await text_channel.send(Constants.NOT_IN_VOICE_CHANNEL_MSG)    
            return True
        return False

    async def _isBotBusy(self, text_channel):
        if self.voice.isVoiceClientPlaying():
            await text_channel.send(Constants.BOT_BUSY)    
            return True
        return False
            
    def _inputValid(self, the_input):
        the_input2 = the_input[1].split(" ") if len(the_input) > 1 else ""
        if not len(the_input2) == 2:
            return False
        return True
    
    async def _startRadioStreaming(self, the_input, member, text_channel):
        try:
            city = the_input[0]
            radio_id = int(the_input[1]) - 1
            f = open("radio_stations.json", "r")
            radios = json.loads(f.read())
            f.close()
            selected_city = radios[city]
            selected_radio_url = selected_city["items"][radio_id]["link"]
            await self.voice.playStreamingRadio(selected_radio_url, member, text_channel)
        except Exception as e:
            print(str(e))
            await text_channel.send("El numero de radio o la ciudad no existen")    
    
    async def handleChangeRadio(self, message, text_channel):
        if await self._isUserInVoiceChannel(message.author.voice, text_channel):
            return
        if not self.voice.isVoiceClientPlaying():
            await text_channel.send("El bot no esta reproduciendo radio")
        the_input = message.content.lower().split("-change-radio ")
        if self._inputValid(the_input):
            self.voice.stopPlayer()
            self.voice.interruptStreaming()
            await self._startRadioStreaming(the_input[1].split(" "), message.author, text_channel)
        else:
            await text_channel.send("-change-radio [ciudad] [numero de radio]")
            await self.handleShowRadios(text_channel)  
    
    async def handleStreamingRadio(self, message, text_channel):
        if await self._isUserInVoiceChannel(message.author.voice, text_channel) and await self._isBotBusy(text_channel):
            return
        the_input = message.content.lower().split("-start-radio ")
        if self._inputValid(the_input):
            await self._startRadioStreaming(the_input[1].split(" "), message.author, text_channel)
        else:
            await text_channel.send("-start-radio [ciudad] [numero de radio]")
            await self.handleShowRadios(text_channel)  
        
    async def handleStopStreamingRadio(self, message, text_channel):
        await self.voice.stopStreaming()
            
    async def handleTextToVoiceTranslation(self, message, text_channel):
        if await self._isUserInVoiceChannel(message.author.voice, text_channel) and await self._isBotBusy(text_channel):
            return
        the_input = message.content.lower().split("-say ")
        if len(the_input) > 1:
            if len(the_input[1]) > 250:
                await text_channel.send(Constants.TEXT_TOO_BIG)
                return
            network_utils = NetworkUtils()
            audio_filename =  ""
            if "/f/" in the_input[1]: #to make female voice 1
                the_input[1] = the_input[1].replace("/f/", "")
                audio_filename = await network_utils.getAndSaveTtsLoquendoVoice(the_input[1], voice="Monica")
            elif "/f2/" in the_input[1]: #to make female voice 2
                the_input[1] = the_input[1].replace("/f2/", "")
                audio_filename = await network_utils.getAndSaveTtsLoquendoVoice(the_input[1], voice="Marisol")
            else:
                audio_filename = await network_utils.getAndSaveTtsLoquendoVoice(the_input[1])
            if audio_filename != "":
                await self.voice.reproduceFromFile(message.author, audio_filename)
            else:
                text_channel.send(Constants.SMTH_FUCKED_UP)
        else:
            await text_channel.send(Constants.BAD_FORMATTED_SAY)
            
    async def handleCustomMessages(self, message, text_channel):
        the_message = message.content.lower()
        if the_message == "buenas noches":
            if message.author.voice == None:
                return
            await self.voice.sayGoodNight(message.author)
        elif "quieres" in the_message:
            await self.handleWant(the_message, text_channel)
    
    async def handleWant(self, message, text_channel):
        if len(message.split(" ")) >= 2:
            options = ["si", "no", "tal vez", "deja de preguntar huevadas conchadetumadre", "anda chambea", "estas cagado del cerebro"]
            random_idx = random.randint(0, len(options) - 1)
            await text_channel.send(f"{options[random_idx]}")
        else:
            await text_channel.send(Constants.BAD_FORMATTED_QUESTION)
            
    async def saluteNewMember(self, member, text_channel):
        await text_channel.send(f"Hola {member.display_name}, bienvenido a este canal de mierda")
        
    async def handleOnResumed(self, text_channel):
        await text_channel.send(Constants.INT_GONE_BUT_BACK) 
        
    async def formatHelpMessage(self, text_channel):
        await text_channel.send("``-subscribe [tag] 'Subscribirse a un webon para cuando entre a discord'``\n" + 
                                "``-unsubscribe [tag] 'Desuscribirse'``\n" +
                                "``-dailyquote [quote diario] 'Mensaje diario del bot'``\n" +
                                "``-set-alert [Link de juego G2A o item de amazon] [rango de precios objetivo] [Moneda(USD o EUR)] 'Alerta de precios en amazon o G2A'``\n" +
                                "``-unset-alert [Link de juego G2A o item de amazon]``\n" +
                                "``-audio-off  'Desactiva tu saludo'``\n" +
                                "``-audio-on 'Activa tu saludo'``\n" +
                                "``-say [texto a decir]``\n" +
                                "``-start-radio [ciudad] [id de radio]``\n" +
                                "``-change-radio [ciudad] [id de radio]``\n" +
                                "``-show-radios 'Muestra las radios disponibles'``\n" +
                                "``-stop-radio``\n"
                                )
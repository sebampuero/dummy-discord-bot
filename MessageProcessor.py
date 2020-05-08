import random
from Utils.NetworkUtils import NetworkUtils

class MessageProcessor():
    
    def __init__(self, voice, subscription, quote, alert, server_manager):
        self.voice = voice
        self.subscription = subscription
        self.quote = quote
        self.alert = alert
        self.server_manager = server_manager
        self.current_guild = None
        
    def set_guild(self, guild):
        self.guild = guild
        
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
        else:
            await self.handleCustomMessages(message, text_channel)
            
    async def handleTextToVoiceTranslation(self, message, text_channel):
        the_input = message.content.lower().split("-say ")
        if len(the_input) > 1:
            network_utils = NetworkUtils()
            audio_filename = network_utils.getAndSaveTtsLoquendoVoice(the_input[1])
            if audio_filename != "":
                await text_channel.send(f"Reproduciendo audio en el canal de voz de {message.author.name}")
                await self.voice.reproduceFromFile(message.author, self.guild, audio_filename)
            else:
                await text_channel.send("Algo salio mal")    
        else:
            await text_channel.send("Formatea bien tu texto, pon `-say [texto a decir en voz]`")
            
    async def handleCustomMessages(self, message, text_channel):
        the_message = message.content.lower()
        if the_message == "buenas noches":
            await self.voice.sayGoodNight(message.author, self.guild)
        elif "quieres" in the_message:
            await self.handleWant(the_message, text_channel)
    
    async def handleWant(self, message, text_channel):
        if len(message.split(" ")) >= 2:
            options = ["si", "no", "tal vez", "deja de preguntar huevadas conchadetumadre", "anda chambea", "estas cagado del cerebro"]
            random_idx = random.randint(0, len(options) - 1)
            await text_channel.send(f"{options[random_idx]}")
        else:
            await text_channel.send("Formula bien tu pregunta cojudo")
            
    async def saluteNewMember(self, member, text_channel):
        await text_channel.send(f"Hola {member.display_name}, bienvenido a este canal de mierda")
        
    async def formatHelpMessage(self, text_channel):
        await text_channel.send(f"""```
                                \n-subscribe [tag] 
                                \n-unsubscribe [tag] 
                                \n-dailyquote [quote diario] 
                                \n-set-alert [Link de juego G2A] [rango de precios objetivo] [Moneda(USD o EUR)]
                                \n-unset-alert [Link de juego G2A]
                                \n-audio-off -> Desactiva tu saludo
                                \n-audio-on -> Activa tu saludo
                                \n-say [texto a decir por voz]
                                ```""")
import random

class MessageProcessor():
    
    def __init__(self):
        pass
    
    async def handleCustomMessage(self, message, text_channel):
        if len(message.split(" ")) >= 2:
            options = ["si", "no", "tal vez", "deja de preguntar huevadas conchadetumadre", "anda chambea", "estas cagado del cerebro"]
            random_idx = random.randint(0, len(options) - 1)
            await text_channel.send(f"{options[random_idx]}")
        else:
            await text_channel.send("Formula bien tu pregunta cojudo")
            
    async def saluteNewMember(self, member, text_channel):
        await text_channel.send(f"Hola {member.display_name}, bienvenido a este canal de mierda")
        
    async def formatHelpMessage(self, text_channel):
        await text_channel.send(f"```-subscribe [tag] \n-unsubscribe [tag] \n-dailyquote [quote diario] \n-set-alert [Link de juego G2A] [rango de precios objetivo] [Moneda(USD o EUR)]\n-unset-alert [Link de juego G2A]```")
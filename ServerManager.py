import asyncio

class ServerManager():
    
    def __init__(self):
        pass
    
    async def showServerStats(self, client, guild, text_channel):
        await client.wait_until_ready()
        while not client.is_closed():
            try:
                await asyncio.sleep(7200)
                in_activity, online, idle, offline = self.getReport(guild)
                await text_channel.send(f"```En discord: {online} huevones.\nHaciendo ni mierda: {idle} huevones.\nJugando algo: {in_activity} huevones.\nOffline: {offline} huevones```")
            except Exception as e:
                print(str(e) + " but no problem for server stats")
                await asyncio.sleep(5)

    def getReport(self, guild):
        online = 0
        idle = 0
        offline = 0
        in_activity = 0
        for m in guild.members:
            if not m.bot:
                if str(m.status) == "online" or str(m.status) == "idle" or str(m.status) == "do_not_disturb" and not str(m.status) == "offline":
                    online += 1
                if str(m.status) == "offline":
                    offline += 1
                if len(m.activities) > 0:
                    for activity in m.activities:
                        if str(activity.type) == "ActivityType.playing":
                            in_activity += 1 
                if len(m.activities) == 0:
                    idle += 1
        return in_activity, online, idle, offline
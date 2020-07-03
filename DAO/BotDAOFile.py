import json

class BotDAOFile():

    def get_radios(self):
        f = open("./config/radio_stations.json", "r")
        radios = json.loads(f.read())
        f.close()
        return radios

    def get_users_welcome_audios(self):
        f = open("./config/users_audio_map.json", "r")
        user_ids_to_audio_map = json.load(f)
        f.close()
        return user_ids_to_audio_map

    def save_radios(self, radios_new):
        with open("./config/radio_stations.json", 'w', encoding='utf-8') as f:
            json.dump(radios_new, f, ensure_ascii=False, indent=4)

    def save_users_welcome_audios(self, new_):
        with open("./config/users_audio_map.json", 'w', encoding='utf-8') as f:
            json.dump(new_, f, ensure_ascii=False, indent=4)
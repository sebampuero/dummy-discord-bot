import discord

class VoiceEmbeds(discord.Embed):

    def __init__(self, author, **options):
        kwargs = {'colour': discord.Color.blue()}
        kwargs.update(options)
        super().__init__(**kwargs)
        self.set_author(name=author.display_name)

    @classmethod
    def from_dict(cls, data):
        options_voice = {
            'color': 1127128
        }
        options_voice.update(data)
        return super().from_dict(options_voice)
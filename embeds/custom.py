from discord import Colour, Embed

class VoiceEmbeds(Embed):

    def __init__(self, author, **options):
        kwargs = {'colour': Colour.blue().value}
        kwargs.update(options)
        super().__init__(**kwargs)
        self.set_author(name=author.display_name)

    @classmethod
    def from_dict(cls, data):
        options_voice = {
            'color': Colour.blue().value
        }
        options_voice.update(data)
        return super().from_dict(options_voice)

class HelpEmbed(Embed):

    @classmethod
    def from_dict(cls, data):
        help_data = {
            'color': Colour.green().value
        }
        help_data.update(data)
        return super().from_dict(help_data)
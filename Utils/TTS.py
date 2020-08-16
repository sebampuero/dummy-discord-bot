from gtts import gTTS

class TTS:

    @classmethod
    def get_tts_url(cls, text, language):
        tts_es = gTTS(text, lang=language)
        url = tts_es.get_urls()[0]
        return url
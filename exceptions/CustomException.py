
class GameException(Exception):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class InvalidTTTMoveException(GameException):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
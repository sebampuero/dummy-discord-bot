class TimeUtils:

    @classmethod
    def parse_seconds(cls, seconds):
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)

        duration = []
        if hours > 0:
            duration.append('{}h'.format(hours))
        if minutes > 0:
            duration.append('{}m'.format(minutes))
        if seconds > 0:
            duration.append('{}s'.format(seconds))

        return ':'.join(duration)
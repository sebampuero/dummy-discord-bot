import re
from exceptions.CustomException import NotValidSongTimestamp

class TimeUtils:

    # 1h:19m:20s for example, or 19m:20s or 20s
    stream_timestamp_pattern = r'^(([1-9]{1}h:)?(([1-5]{1})?[0-9]{1}m:)?(([1-5]{1})?[0-9]{1}s))$'

    @classmethod
    def parse_seconds(cls, seconds):
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)

        duration = []
        if days > 0:
            duration.append('{} days'.format(days))
        if hours > 0:
            duration.append('{} hours'.format(hours))
        if minutes > 0:
            duration.append('{} minutes'.format(minutes))
        if seconds > 0:
            duration.append('{} seconds'.format(seconds))

        return ', '.join(duration)

    @classmethod
    def parse_readable_format(cls, timestamp):
        if not re.match(cls.stream_timestamp_pattern, timestamp):
            raise NotValidSongTimestamp(f"{timestamp} is not a valid timestamp")
        parts = timestamp.split(":")
        seconds = 0
        for el in parts:
            if "s" in el:
                seconds += int(el[:-1])
            elif "m" in el:
                seconds += int(el[:-1]) * 60
            elif "h" in el:
                seconds += int(el[:-1]) * 3600
        return seconds

import logging

class Query:

    def __init__(self, the_query, filename=None):
        self.data = None
        self.the_query = the_query

    def set_data(self, data):
        self.data = data

    def __repr__(self):
        return self.the_query

class LocalMP3Query(Query):

    def __init__(self, filename, url,  author_name):
        self.title = f"{filename} puesto por {author_name}"
        super().__init__(url)

    def __repr__(self):
        return self.title

class YoutubeQuery(Query):

    def __init__(self, the_query):
        super().__init__(the_query)

    def __repr__(self):
        return " ".join(self.the_query) if isinstance(self.the_query, tuple) or isinstance(self.the_query, list) else self.the_query

class SpotifyQuery(Query):

    def __init__(self, the_query):
        super().__init__(the_query)

class SoundcloudQuery(Query):

    def __init__(self, the_query):
        super().__init__(the_query)
import logging

class Query:

    def __init__(self, the_query):
        self.the_query = the_query

    def __repr__(self):
        return self.the_query

class LocalMP3Query(Query):

    def __init__(self, the_query, author_name):
        self.title = f"{the_query} puesto por {author_name}"
        super().__init__(the_query)

    def __repr__(self):
        return self.title

class YoutubeQuery(Query):

    def __init__(self, the_query):
        super().__init__(the_query)

    def __repr__(self):
        return f'Busqueda de youtube: `{" ".join(self.the_query)}`'

class SpotifyQuery(Query):

    def __init__(self, the_query):
        super().__init__(the_query)

class SoundcloudQuery(Query):

    def __init__(self, the_query):
        super().__init__(the_query)
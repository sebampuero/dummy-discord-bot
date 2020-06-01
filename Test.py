from spotipy.oauth2 import SpotifyClientCredentials
import spotipy
import json

f = open("spotify.txt", "r")
creds = f.read().split(",")
client_credentials_manager = SpotifyClientCredentials(client_id=creds[0], client_secret=creds[1])
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
f.close()

playlist_id = 'https://open.spotify.com/playlist/37i9dQZF1DX9ZKyQHcEFXZ?si=K5pli5U7Sua5ivkKtVFj3Q'
def process_query_object_for_spotify_playlist(query):
    query_tracks_list = []
    results = sp.playlist(query)
    items_list = results['tracks']['items']
    for item in items_list:
        track_obj = {}
        a_item = item["track"]
        track_obj["name"] = a_item["name"]
        track_obj["artists"] = a_item["artists"]
        query_tracks_list.append(track_obj)
    return query_tracks_list

a_list = process_query_object_for_spotify_playlist(playlist_id)
while len(a_list) > 0:
    track_obj = a_list.pop()
    query_for_yt = track_obj["name"] + " "
    for artist in track_obj["artists"]:
        query_for_yt += artist["name"] + " "
    print(query_for_yt)
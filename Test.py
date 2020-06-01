from spotipy.oauth2 import SpotifyClientCredentials
import spotipy
import json

client_credentials_manager = SpotifyClientCredentials()
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

playlist_id = 'https://open.spotify.com/playlist/37i9dQZF1DX8SfyqmSFDwe?si=FYVQzFDrS4ebs9QI0rfcug'
results = sp.playlist(playlist_id)
f = open("results.json", "w")
f.write(json.dumps(results, indent=4))
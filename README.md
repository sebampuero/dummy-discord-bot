# Multifunctional Discord bot

Discord bot made with the Discord API Wrapper [discord.py](https://discordpy.readthedocs.io/en/latest/index.html)

Current functions:
* Music playback using YoutubeDL + ability to save spotify playlists
* Radio playback + ability to add new radio links (must be Content-Type mp3 or aac)
* Welcome audios for guild members when they join a voice channel + ability to add new audios for every guild member
* TTS
* Subscription to other guild member (notifications when someone enters a voice channel)
* Price alert system for Amazon US, Amazon EU and G2A
* Tic tac toe vs other gulld members or AI

Future wishes:
* Tests coverage to at least 80% (current: 0%)

Feel free to clone the project and test the bot locally or in a remote server. 

# Installation

* First, clone the repo and install the requirements with `pip install -r requirements.txt`
* You'll need a token to run the bot. Store the token under a file called `token.txt` in the root directory. The DB password will be stored under `password.txt`
* Other services used require credentials. Spotify, soundclound and Twillio credentials are stored in `config/creds.json`.
* If using Twillio for the Whatsapp API which is used for logging, a `phone_numbers.json` file will be needed under `config/phone_numbers.json`

# Tests

* For DB testing, Docker is to be used.
* Go to `Tests/` and run `docker run -d -p 3307:3306 .` to initialize the MySQL Container

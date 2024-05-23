# app.py
from flask import Flask, jsonify, request
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
import os

app = Flask(__name__)

sp = Spotify(auth_manager=SpotifyOAuth(client_id=os.getenv("SPOTIPY_CLIENT_ID"),
                                       client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
                                       redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
                                       scope="user-read-currently-playing"))

@app.route('/currently-playing', methods=['GET'])
def currently_playing():
    current_track = sp.current_user_playing_track()
    if current_track is None:
        return jsonify({'error': 'No track currently playing'})

    track_id = current_track['item']['id']
    features = sp.audio_features(track_id)[0]
    track_info = {
        'name': current_track['item']['name'],
        'artist': current_track['item']['artists'][0]['name'],
        'album': current_track['item']['album']['name'],
        'genre': current_track['item']['album']['genres'],  # This might require additional handling
        'bpm': features['tempo'],
        'key': features['key'],
        'mode': features['mode'],
        'duration_ms': features['duration_ms']
    }
    return jsonify(track_info)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

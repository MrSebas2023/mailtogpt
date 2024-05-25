from flask import Flask, jsonify, send_from_directory
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
import os
import logging

app = Flask(__name__, static_folder='static')

logging.basicConfig(level=logging.DEBUG)

sp_oauth = SpotifyOAuth(
    client_id=os.getenv("SPOTIPY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
    redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
    scope="user-read-currently-playing"
)

@app.route('/')
def home():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/login')
def login():
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route('/callback')
def callback():
    session.clear()
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session["token_info"] = token_info
    return redirect(url_for('currently_playing'))

@app.route('/currently-playing', methods=['GET'])
def currently_playing():
    try:
        token_info = get_token()
        sp = Spotify(auth=token_info['access_token'])
        logging.debug("Fetching currently playing track.")
        current_track = sp.current_user_playing_track()
        logging.debug(f"Spotify response: {current_track}")
        if current_track is None or not current_track.get('item'):
            logging.debug("No track currently playing.")
            return jsonify({'error': 'No track currently playing'})

        track_id = current_track['item']['id']
        features = sp.audio_features(track_id)[0]
        track_info = {
            'name': current_track['item']['name'],
            'artist': current_track['item']['artists'][0]['name'],
            'album': current_track['item']['album']['name'],
            'bpm': features['tempo'],
            'key': features['key'],
            'mode': features['mode'],
            'duration_ms': features['duration_ms']
        }
        logging.debug(f"Track info: {track_info}")
        return jsonify(track_info)
    except Exception as e:
        logging.error(f"Error fetching currently playing track: {e}")
        return jsonify({'error': 'Failed to fetch currently playing track'})

def get_token():
    token_info = session.get("token_info", None)
    if not token_info:
        raise Exception("No token found")
    if sp_oauth.is_token_expired(token_info):
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
    return token_info

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
from flask import Flask, redirect, url_for, session, request, jsonify, send_from_directory
from flask_session import Session
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
import requests
import logging
import time

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './.flask_session/'
Session(app)

# Spotify credentials
SPOTIPY_CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID', 'your_client_id')
SPOTIPY_CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET', 'your_client_secret')
SPOTIPY_REDIRECT_URI = os.getenv('SPOTIPY_REDIRECT_URI', 'your_redirect_uri')

# Ensure the scope includes all necessary permissions
scope = "user-library-read playlist-modify-public playlist-modify-private user-read-playback-state user-read-currently-playing"

sp_oauth = SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET, redirect_uri=SPOTIPY_REDIRECT_URI, scope=scope)

# In-memory storage for history
history = []

def get_token():
    token_info = session.get('token_info', None)
    if not token_info:
        return None

    now = int(time.time())
    is_expired = token_info['expires_at'] - now < 60

    if is_expired:
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        session['token_info'] = token_info

    return token_info

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/currently-playing', methods=['GET'])
def currently_playing():
    token_info = get_token()
    if not token_info:
        return jsonify({'error': 'User not authenticated'}), 401

    sp = spotipy.Spotify(auth=token_info['access_token'])
    current_track = sp.current_playback()
    
    if current_track and current_track['is_playing']:
        track = current_track['item']
        audio_features = sp.audio_features([track['id']])[0]
        track_info = {
            'name': track['name'],
            'artist': ', '.join([artist['name'] for artist in track['artists']]),
            'album': track['album']['name'],
            'album_image_url': track['album']['images'][0]['url'],
            'id': track['id'],
            'bpm': audio_features['tempo'],
            'key': audio_features['key'],
            'mode': 'Major' if audio_features['mode'] == 1 else 'Minor',
            'genre': 'example genre'  # Placeholder for genre information
        }

        # Add to history if not already present
        if not any(t['id'] == track_info['id'] for t in history):
            history.append(track_info)

        return jsonify(track_info)
    else:
        return jsonify({'error': 'No track currently playing'})

@app.route('/history', methods=['GET'])
def get_history():
    return jsonify(history)

@app.route('/login')
def login():
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route('/callback')
def callback():
    session.clear()
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session['token_info'] = token_info
    return redirect(url_for('index'))

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    app.run(host='0.0.0.0', port=5000, debug=True)

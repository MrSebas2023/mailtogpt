from flask import Flask, redirect, url_for, session, request, jsonify, send_from_directory
from flask_session import Session
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
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
scope = "user-library-read playlist-modify-public playlist-modify-private user-read-playback-state user-modify-playback-state"

sp_oauth = SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET, redirect_uri=SPOTIPY_REDIRECT_URI, scope=scope)

# In-memory storage for history
track_history = []

def create_or_get_playlist(sp, playlist_name):
    playlists = sp.current_user_playlists()
    for playlist in playlists['items']:
        if (playlist['name']).lower() == playlist_name.lower():
            return playlist['id']
    
    new_playlist = sp.user_playlist_create(user=sp.current_user()['id'], name=playlist_name)
    return new_playlist['id']

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

@app.route('/history')
def history():
    return jsonify(track_history[:5])  # Return only the last 5 tracks

@app.route('/currently-playing', methods=['GET'])
def currently_playing():
    token_info = get_token()
    if not token_info:
        return jsonify({'error': 'User not authenticated'}), 401
    
    sp = spotipy.Spotify(auth=token_info['access_token'])
    current_track = sp.current_playback()
    if current_track and current_track['is_playing']:
        track = current_track['item']
        track_id = track['id']
        
        # Fetch audio features
        audio_features = sp.audio_features([track_id])[0]
        bpm = round(audio_features['tempo'])  # Round the BPM to the nearest integer
        key = audio_features['key']
        mode = 'Major' if audio_features['mode'] == 1 else 'Minor'
        
        # Fetch artist's genres
        artist_id = track['artists'][0]['id']
        artist_info = sp.artist(artist_id)
        genres = artist_info['genres']
        
        track_info = {
            'name': track['name'],
            'artist': ', '.join([artist['name'] for artist in track['artists']]),
            'album': track['album']['name'],
            'album_image_url': track['album']['images'][0]['url'],
            'id': track_id,
            'genre': genres,
            'bpm': bpm,
            'key': key,
            'mode': mode
        }

        # Add to history at the beginning
        if not any(t['id'] == track_info['id'] for t in track_history):
            track_history.insert(0, track_info)
            if len(track_history) > 5:
                track_history.pop()  # Keep only the last 5 tracks
        
        return jsonify(track_info)
    else:
        return jsonify({'error': 'No track currently playing'})

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

@app.route('/add_to_playlist/<genre>', methods=['POST'])
def add_to_playlist(genre):
    token_info = get_token()
    if not token_info:
        return jsonify({'error': 'User not authenticated'}), 401
    
    sp = spotipy.Spotify(auth=token_info['access_token'])
    track_id = request.json['track_id']
    
    playlist_name = genre
    
    playlist_id = create_or_get_playlist(sp, playlist_name)
    sp.playlist_add_items(playlist_id, [track_id])
    
    return jsonify({'success': True, 'message': f'Track added to {playlist_name}'})

@app.route('/play_track/<track_id>', methods=['POST'])
def play_track(track_id):
    token_info = get_token()
    if not token_info:
        return jsonify({'error': 'User not authenticated'}), 401

    sp = spotipy.Spotify(auth=token_info['access_token'])
    
    # Add track to the queue
    sp.add_to_queue(uri=f'spotify:track:{track_id}')
    
    # Skip to the next track to start playing the queued track
    sp.next_track()
    
    return jsonify({'success': True, 'message': 'Track is now playing'})

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    app.run(host='0.0.0.0', port=5000, debug=True)

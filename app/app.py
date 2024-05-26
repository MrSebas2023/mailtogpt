from flask import Flask, redirect, url_for, session, request, jsonify
from flask_session import Session
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
import requests

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

SPOTIPY_CLIENT_ID = 'your_client_id'
SPOTIPY_CLIENT_SECRET = 'your_client_secret'
SPOTIPY_REDIRECT_URI = 'your_redirect_uri'

scope = "user-library-read playlist-modify-public playlist-modify-private"

sp_oauth = SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET, redirect_uri=SPOTIPY_REDIRECT_URI, scope=scope)

def create_or_get_playlist(sp, playlist_name):
    playlists = sp.current_user_playlists()
    for playlist in playlists['items']:
        if playlist['name'] == playlist_name:
            return playlist['id']
    
    new_playlist = sp.user_playlist_create(user=sp.current_user()['id'], name=playlist_name)
    return new_playlist['id']

def is_track_in_lexicon(track_id):
    lexicon_url = "http://192.168.2.16:48624/v1/tracks"
    response = requests.get(lexicon_url)
    if response.status_code == 200:
        tracks = response.json()
        for track in tracks:
            if track['id'] == track_id:
                return True
    return False

@app.route('/')
def index():
    if 'token_info' in session:
        token_info = session['token_info']
        sp = spotipy.Spotify(auth=token_info['access_token'])
        current_track = sp.current_playback()
        if current_track and current_track['is_playing']:
            track = current_track['item']
            track_info = {
                'name': track['name'],
                'artist': ', '.join([artist['name'] for artist in track['artists']]),
                'album': track['album']['name'],
                'cover_url': track['album']['images'][0]['url'],
                'id': track['id'],
                'in_lexicon': is_track_in_lexicon(track['id'])
            }
            return jsonify(track_info)
        else:
            return jsonify({'error': 'No track currently playing'})
    else:
        return redirect(url_for('login'))

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
    if 'token_info' in session:
        token_info = session['token_info']
        sp = spotipy.Spotify(auth=token_info['access_token'])
        track_id = request.json['track_id']
        
        if is_track_in_lexicon(track_id):
            playlist_name = f"{genre}-exist"
        else:
            playlist_name = genre
        
        playlist_id = create_or_get_playlist(sp, playlist_name)
        sp.playlist_add_items(playlist_id, [track_id])
        
        return jsonify({'success': True, 'message': f'Track added to {playlist_name}'})
    else:
        return jsonify({'error': 'User not authenticated'}), 401

if __name__ == '__main__':
    app.run(debug=True)

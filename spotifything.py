import discord
import sqlite3
import spotipy
import creds
from datetime import datetime

client = discord.Client()

scope = 'playlist-modify-public'

sp_oauth = spotipy.oauth2.SpotifyOAuth(creds.spot_id, creds.spot_secret, 'http://localhost/', scope=scope, cache_path='./spotipy_oauth_cache')
token_info = sp_oauth.get_cached_token()

if token_info:
    print ("Found cached token...")
    spot_token = token_info['access_token']
else:
    response_url = input("Enter URL: ")
    code = sp_oauth.parse_response_code(response_url)
    if code:
        print ("Auth code retrieved from provided URL...")
        token_info = sp_oauth.get_access_token(code)
        spot_token = token_info['access_token']
sp = spotipy.Spotify(auth=spot_token)

def refresh_token():
    global token_info, sp
    if sp_oauth.is_token_expired(token_info):
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        spot_token = token_info['access_token']
        sp = spotipy.Spotify(auth=spot_token)
    return sp

def spot_checks(before, after):
    user = str(after)
    guild = after.guild
    sound_role = guild.get_role(699545807338078248)
    user_roles = after.roles
    user_activities = []

    act_string = 'Updating activity for {0}...'.format(user)
    print(act_string)

    for spot in after.activities:
        user_activities.append(spot.name)
        if str(spot) == 'Spotify':
            spot_string = '{0} is listening to Spotify...'.format(user)
            print(spot_string)

            if sound_role in user_roles:
                song_pos = datetime.utcnow() - spot.start
                song_pos_seconds = song_pos.total_seconds()

                c.execute('SELECT id FROM tunes WHERE id = ?', (spot.track_id,))
                queryresult = c.fetchall()
                
                if len(queryresult) == 0:
                    c.execute('INSERT INTO tunes VALUES (?, ?, ?, ?, 1)', (spot.track_id, spot.title, spot.artist, user))
                    conn.commit()
                    add_string = '[ + ] Added {0} by {1} with ID {2} to database. Overheard from {3}.\n '.format(spot.title, spot.artist, spot.track_id, user)
                    track_array = [spot.track_id]
                    sp.user_playlist_add_tracks(creds.spot_user, creds.spot_playlist, track_array)
                    print(add_string)
                    
                elif len(queryresult) == 1:
                    if song_pos_seconds <= 5:
                        c.execute('SELECT count FROM tunes WHERE id = ?', (spot.track_id,))
                        count = c.fetchone()[0]
                        count += 1
                        c.execute('UPDATE tunes SET count=? WHERE id = ?', (count, spot.track_id))
                        conn.commit()
                        count_string = '[ O ] Recognised {0} by {1} with ID {2}. Overheard from {3}, at a total of {4} times.\n '.format(spot.title, spot.artist, spot.track_id, user, count)
                        print(count_string)
                    else:
                        resume_string = '{0} has resumed listening to {1} by {2}.\n'.format(user, spot.title, spot.artist)
                        print(resume_string)

                else:
                    bad_string = '[ X ] {0} by {1} has somehow appeared twice in the database. Panic.'.format(spot.title, spot.artist)
                    print(bad_string)

            else:
                no_role_string = '{0} does not have the Sound role.\n'.format(user)
                print(no_role_string)
                
            return

    no_spotify_string = '{0} is not listening to Spotify. (Activities: {1})\n'.format(user, user_activities)
    print(no_spotify_string)
        
    return

print('Spotify enabled...')


conn = sqlite3.connect('tunes.db')
c = conn.cursor()

'''
c.execute('CREATE TABLE tunes (id TEXT, title TEXT, artist TEXT, user TEXT, count INTEGER)')
conn.commit()
'''

@client.event
async def on_member_update(before, after):

    sp = refresh_token()
    spot_checks(before, after)
    
    

@client.event
async def on_ready():
    print('\nListening...')

disc_token = creds.bot_token
client.run(disc_token)

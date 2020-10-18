#!/usr/bin/env python3

import discord # https://github.com/Rapptz/discord.py
import sqlite3
import spotipy # https://github.com/plamere/spotipy
import creds
import os
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

def refresh_token(): # Ensures the bot always has valid spotify auth to make changes with
    global token_info, sp
    if sp_oauth.is_token_expired(token_info):
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        spot_token = token_info['access_token']
        sp = spotipy.Spotify(auth=spot_token)
    return sp

def spot_checks(before, after): # The meat of the program
    user = str(after)
    guild = after.guild
    sound_role = guild.get_role(creds.role_id)
    user_roles = after.roles
    user_activities = []

    act_string = 'Updating activity for {0}...'.format(user)
    print(act_string)

    for act in after.activities:
        user_activities.append(act.name)
        if str(act) == 'Spotify':
            spot_string = '{0} is listening to Spotify...'.format(user)
            print(spot_string)

            if sound_role in user_roles: # Only adds songs from people with a given role, so you can filter out those with poor taste
                song_pos = datetime.utcnow() - act.start # How far the user is into their current song
                song_pos_seconds = song_pos.total_seconds()

                c.execute('SELECT id FROM tunes WHERE id = ?', (act.track_id,))
                queryresult = c.fetchall()
                
                if len(queryresult) == 0: # tl;dr: if song not in database, add it
                    c.execute('INSERT INTO tunes VALUES (?, ?, ?, ?, 1)', (act.track_id, act.title, act.artist, user))
                    conn.commit()
                    add_string = '[ + ] Added {0} by {1} with ID {2} to database. Overheard from {3}.\n '.format(act.title, act.artist, act.track_id, user)
                    track_array = [act.track_id]
                    sp.user_playlist_add_tracks(creds.spot_user, creds.spot_playlist, track_array)
                    print(add_string)
                    
                elif len(queryresult) == 1: # tl;dr: if song in database, increment count
                    if song_pos_seconds <= 5: # Only increments when user is less than 5 seconds into the track, otherwise it would increment every time they pause
                        c.execute('SELECT count FROM tunes WHERE id = ?', (act.track_id,))
                        count = c.fetchone()[0]
                        count += 1
                        c.execute('UPDATE tunes SET count=? WHERE id = ?', (count, act.track_id))
                        conn.commit()
                        count_string = '[ O ] Recognised {0} by {1} with ID {2}. Overheard from {3}, at a total of {4} times.\n '.format(act.title, act.artist, act.track_id, user, count)
                        print(count_string)
                    else: # This is really just debugging output that looks nice on the readout
                        resume_string = '{0} has resumed listening to {1} by {2}.\n'.format(user, act.title, act.artist)
                        print(resume_string)

                else: # Just in case - you never know what might go wrong...
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

if not os.path.isfile("tunes.db"): # Establishes a new database if needed
    print("No file named tunes.db found, creating new table...")
    conn = sqlite3.connect('tunes.db')
    c = conn.cursor()
    c.execute('CREATE TABLE tunes (id TEXT, title TEXT, artist TEXT, user TEXT, count INTEGER)')
    conn.commit()
else:
    print("Located tunes.db...")
    conn = sqlite3.connect('tunes.db')
    c = conn.cursor()

@client.event
async def on_member_update(before, after):

    sp = refresh_token()
    spot_checks(before, after)
    
    

@client.event
async def on_ready():
    print('\nListening...')

disc_token = creds.bot_token
client.run(disc_token)

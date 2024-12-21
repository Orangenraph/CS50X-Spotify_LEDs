import tinytuya
import spotipy
import json
import time
import requests
import colorsys
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
import os

from cs50 import SQL

from flask import Flask, flash, redirect, render_template, request, session, url_for, jsonify, Response

from flask_session import Session

from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, login_required, device_required
from urllib.parse import quote

from spotipy.oauth2 import SpotifyOAuth

app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False # Sitzung schließt nach Browsers löschen
app.config["SESSION_TYPE"] = "filesystem" # Speichert Sitzungsdaten als temporäre Dateien auf dem Server (anstelle von Cookies)
TOKEN_INFO = "token_info"
Session(app)

db = SQL("sqlite:///SQLite")

# App stets aktuelle Inhalte liefert.
@app.after_request # nachdem die App eine HTTP-Antwort erstellt hat.
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate" # Verhindert, dass Browser oder Proxy-Server die Seite zwischenspeichern.
    response.headers["Expires"] = 0 # Unterstützen ältere Browser bei der Deaktivierung des Caches.
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/", methods=['GET', 'POST'])
@login_required
def index():
    ''' MAIN '''
    user_id = session["user_id"]
    print(f"user_id; {user_id}")

    # Überprüft ob das Licht an ist
    switch_state = db.execute("SELECT lights_on_off FROM user_settings WHERE user_id = ?", user_id)
    switch_state = bool(switch_state[0]['lights_on_off']) if switch_state else False  # Default auf False setzen, wenn nicht vorhanden

    # Überprüft ob das Pasuiert ist
    pause_state = db.execute("SELECT song_on_off FROM user_settings WHERE user_id = ?", user_id)
    pause_state = bool(pause_state[0]['song_on_off']) if pause_state else False

    # Überprüfen, ob ein Gerät für den Benutzer existiert
    device = db.execute("SELECT * FROM device WHERE user_id = ?", user_id)
    # Überprüfen, ob der Benutzer mit Spotify verbunden ist
    spotify_connection = db.execute("SELECT * FROM spotify WHERE user_id = ?", user_id)

    if not device:
        return redirect("/device")
    if not spotify_connection:
        return redirect("/spotify")

    if session.get(TOKEN_INFO) is None:
        return spotify_login()

    track_info = get_current_track()
    save_current_track(track_info, user_id)
    save_genre_colors()

    genre_colors, genres = reorder_colors(user_id)
    pastel_colors = convert_to_pastel(genre_colors)

    update_led_color(track_info, user_id, device)
    tops = stats(user_id)
    barplot = genre_plot(user_id,pastel_colors)

    return render_template(
        "index.html",
        device=device,
        track_info=track_info,
        genres=genres,
        genre_colors=genre_colors,
        pastel_colors=pastel_colors,
        switch_state=switch_state,
        pause_state = pause_state,
        tops=tops,
        barplot=barplot
    )

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    session.clear()

    if request.method == "POST":
        if not request.form.get("username"):
            return apology("must provide username", 403)

        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Check if user has an entry in user_settings
        settings = db.execute(
            "SELECT * FROM user_settings WHERE user_id = ?", session["user_id"]
        )

        # If no entry exists, create one with default values (0, 0)
        if len(settings) == 0:
            db.execute(
                "INSERT INTO user_settings (user_id, lights_on_off, song_on_off) VALUES (?, 0, 0)",
                session["user_id"],
            )


        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()
    #delete_folders()   # UNCOMMAND ME if you only use ONE user  <<<<<<<<<<<<<<-------------------------------------
    #clear_spotify_cache() # UNCOMMAND ME if you only use ONE user <<<<<<<<<<<<<<-------------------------------------

    tinytuya_config = {"apiKey": "?","apiSecret": "?","apiRegion": "?","apiDeviceID": "?"}
    try:
        with open("../tinytuya.json", "w") as json_file:
            json.dump(tinytuya_config, json_file, indent=4)
    except Exception as e:
        return apology(f"Fehler beim Erstellen der tinytuya.json: {str(e)}", 500)

    # Redirect user to login form
    return redirect("/login")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if not username:
            return  apology("Must Provide A Username", 400)

        if not password:
            return  apology("Must Provide A Password", 400)

        if password != confirmation:
            return  apology("Passwords must match", 400)

        hash = generate_password_hash(password)

        try:
            db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, hash)
        except ValueError:
            return  apology("Username already exists", 400)

        return redirect("/login")

    else:
        return render_template("register.html")


@app.route("/device", methods=["GET", "POST"])
@login_required
def device():
    ''' Register User in Databank '''
    success_message = "Not Done"  # Default state is "Not Done"
    tuya_access_id = ""
    tuya_access_key = ""
    device_id = ""
    endpoint = ""

    # Check if device data is already registered in the database
    device_data = db.execute("SELECT * FROM device WHERE user_id = ?", [session["user_id"]])
    if device_data:  # If device data exists
        success_message = "Done"
        tuya_access_id = device_data[0]["TUYA_ACCESS_ID"]
        tuya_access_key = device_data[0]["TUYA_ACCESS_KEY"]
        device_id = device_data[0]["DEVICE_ID"]
        endpoint = device_data[0]["ENDPOINT"]

    if request.method == "POST":
        TUYA_ACCESS_ID = request.form.get("tuya_access_id")
        TUYA_ACCESS_KEY = request.form.get("tuya_access_key")
        DEVICE_ID = request.form.get("device_id")
        ENDPOINT = request.form.get("endpoint")

        if not  TUYA_ACCESS_ID:
            return apology("Internal Tuya Access ID Error", 500)

        if not TUYA_ACCESS_KEY:
            return apology("Internal Tuya Access Key Error", 500)

        if not DEVICE_ID:
            return apology("Must provide device ID", 400)

        try:
            # If device data exists, update it, otherwise insert new data
            if device_data:
                db.execute(
                    "UPDATE device SET TUYA_ACCESS_ID = ?, TUYA_ACCESS_KEY = ?, DEVICE_ID = ?, ENDPOINT = ? WHERE user_id = ?",
                    TUYA_ACCESS_ID, TUYA_ACCESS_KEY, DEVICE_ID, ENDPOINT, session["user_id"])
            else:
                db.execute("INSERT INTO device (user_id, TUYA_ACCESS_ID, TUYA_ACCESS_KEY, DEVICE_ID, ENDPOINT) VALUES (?, ?, ?, ?, ?)",
                    session["user_id"], TUYA_ACCESS_ID, TUYA_ACCESS_KEY, DEVICE_ID, ENDPOINT)
        except Exception as e:
            return apology(f"Error saving device: {str(e)}", 500)

        flash("Smart Device credentials saved successfully!")
        return redirect("/device")

    else:
        return render_template("device.html", success_message=success_message, tuya_access_id=tuya_access_id, tuya_access_key=tuya_access_key, device_id=device_id, endpoint=endpoint)


@app.route("/toggle_device", methods=["POST"])
@device_required
def toggle_device():
    """Toggle device state (on/off)"""
    user_id = session["user_id"]
    action = request.form.get("switch_state") == "on" # "on" oder "off"
    if action:
        check_lights(user_id,1)
    else:
        check_lights(user_id,0)

    try:
        device = db.execute("SELECT * FROM device WHERE user_id = ?", user_id)
    except Exception as e:
        return apology(f"Fehler beim Abrufen des Geräts aus der Datenbank: {str(e)}", 500)

    # Tuya API-Zugangsdaten und Device ID aus der Datenbank

    tinytuya_config = {
        "apiKey": device[0]["TUYA_ACCESS_ID"],
        "apiSecret": device[0]["TUYA_ACCESS_KEY"],
        "apiRegion": device[0]["ENDPOINT"],
        "apiDeviceID": device[0]["DEVICE_ID"]
    }

    # JSON in Datei speichern
    try:
        with open("../tinytuya.json", "w") as json_file:
            json.dump(tinytuya_config, json_file, indent=4)
    except Exception as e:
        return apology(f"Fehler beim Erstellen der tinytuya.json: {str(e)}", 500)


    # Tuya Cloud-Objekt erstellen
    try:
        tuya_cloud = tinytuya.Cloud(apiRegion="eu-w", apiKey=device[0]["TUYA_ACCESS_ID"], apiSecret=device[0]["TUYA_ACCESS_KEY"])

    except Exception as e:
        return apology(f"Error connecting to Tuya Cloud: {str(e)}", 500)

    # Befehl basierend auf der Aktion (on/off)

    commands = {"commands": [{"code": "switch_led", "value": bool(action)}]}

    try:
        tuya_cloud.sendcommand(device[0]["DEVICE_ID"], commands)
        return redirect("/")

    except Exception as e:
        return apology(f"Error controlling device: {str(e)}", 500)


def check_lights(user_id, on_off):
    print("CHECK LIGHTS")
    user_settings = db.execute("SELECT * FROM user_settings WHERE user_id = ?", user_id)

    # Wenn der Benutzer nicht existiert, füge ihn mit lights_on_off = True hinzu
    if not user_settings:
        try:
            db.execute("INSERT INTO user_settings (user_id, lights_on_off) VALUES (?,?)", user_id, on_off)
        except Exception as e:
            return apology(f"Error saving device settings: {str(e)}", 500)
    else:
        # Wenn der Benutzer existiert, aktualisiere den Wert von lights_on_off auf True
        try:
            db.execute("UPDATE user_settings SET lights_on_off = ? WHERE user_id = ?", on_off, user_id)
        except Exception as e:
            return apology(f"Error updating device settings: {str(e)}", 500)

def check_pause(user_id, on_off):
    user_settings = db.execute("SELECT * FROM user_settings WHERE user_id = ?", user_id)

    # Wenn der Benutzer nicht existiert, füge ihn mit lights_on_off = True hinzu
    if not user_settings:
        try:
            db.execute("INSERT INTO user_settings (user_id, song_on_off) VALUES (?, ?)", user_id, on_off)
        except Exception as e:
            return apology(f"Error saving Pause Botton settings: {str(e)}", 500)
    else:
        # Wenn der Benutzer existiert, aktualisiere den Wert von lights_on_off auf True
        try:
            db.execute("UPDATE user_settings SET song_on_off = ? WHERE user_id = ?", on_off, user_id)
        except Exception as e:
            return apology(f"Error saving Pause settings: {str(e)}", 500)


@app.route("/help")
@login_required
def help():
    return render_template("help.html")

@app.route("/delete")
@login_required
def delete():
    user_id = session["user_id"]

    try:
        # Lösche alle relevanten Daten des Benutzers aus den Tabellen
        db.execute("DELETE FROM device WHERE user_id = ?", user_id)
        db.execute("DELETE FROM genre_colors WHERE user_id = ?", user_id)
        db.execute("DELETE FROM spotify WHERE user_id = ?", user_id)
        db.execute("DELETE FROM tracks WHERE user_id = ?", user_id)
        db.execute("DELETE FROM user_settings WHERE user_id = ?", user_id)
        db.execute("DELETE FROM users WHERE id = ?", user_id)
    except Exception as e:

        return f"Deleting Data Error: {e}", 500

    session.clear()
    return redirect("/login")

''' ---------------------------------------------------------  SPOTIFY  ----------------------------------------------------------------------------------------- '''
def create_spotify_oauth(): #Spotify-OAuth-Objekt zu erstellen
    '''Get Spotify credentials from database'''
    print("CREATE SPOTIFY OAUTH")
    user_id = session["user_id"]
    credentials = db.execute("SELECT client_id, client_secret FROM spotify WHERE user_id = ?", user_id)

    if not credentials:
        raise Exception("Spotify credentials not found for user.")

    return SpotifyOAuth(
        client_id=credentials[0]["client_id"],
        client_secret=credentials[0]["client_secret"],
        redirect_uri=url_for('redirectPage', _external=True), #https://developer.spotify.com/documentation/web-api/concepts/scopes 13.12.2024
        scope="user-read-playback-state user-modify-playback-state user-read-currently-playing user-top-read")


def get_token():
    '''aktuelle Spotify-Token aus der Sitzung zu erhalten und bei Bedarf zu aktualisieren.'''
    print("GET TOKEN")

    token_info = session.get(TOKEN_INFO, None)
    if not token_info:
        raise Exception("Token not found in session.")
    now = int(time.time())
    is_expired = token_info['expires_at'] - now < 60
    if is_expired:
        sp_oauth = create_spotify_oauth()
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        session[TOKEN_INFO] = token_info

    print(f" Get_user_info token info: {get_user_info(token_info["access_token"])}")
    print("Session data:", session)
    print(f"Session.sid {session.sid}")  # Funktioniert bei Flask-Session (mit Dateispeicherung)
    return token_info

@app.route("/spotify", methods=["GET", "POST"])
@login_required
def spotify():
    """Register Spotify credentials and redirect to Spotify auth"""

    print("SPOTIFY")
    success_message = "Not Done"
    client_id = ""
    client_secret = ""

    spotify_data = db.execute("SELECT * FROM spotify WHERE user_id = ?", [session["user_id"]])
    if spotify_data:  # Wenn die Spotify-Daten bereits in der Datenbank existieren
        success_message = "Done"
        client_id = spotify_data[0]["client_id"]
        client_secret = spotify_data[0]["client_secret"]

    if request.method == "POST":
        # Get the form data
        client_id = request.form.get("client_id")
        client_secret = request.form.get("client_secret")

        # Check for missing fields
        if not client_id:
            return apology("Must provide Spotify client ID", 400)
        if not client_secret:
            return apology("Must provide Spotify client secret", 400)

        # Save to database
        try:
            if spotify_data:
                # Falls Daten bereits existieren, aktualisiere sie
                db.execute("UPDATE spotify SET client_id = ?, client_secret = ? WHERE user_id = ?",client_id, client_secret, session["user_id"])
            else:
                # Falls keine Daten vorhanden sind, füge sie hinzu
                db.execute("INSERT INTO spotify (user_id, client_id, client_secret) VALUES (?, ?, ?)",session["user_id"], client_id, client_secret)

        except Exception as e:
            return apology(f"Error saving Spotify credentials: {str(e)}", 500)

        flash("Spotify credentials saved successfully!")
        session["spotify_registered"] = True
        return redirect("/spotify")

    else:
        return render_template("spotify.html", success_message=success_message, client_id=client_id, client_secret=client_secret)

@app.route('/redirectPage')
def redirectPage():
    ''' Benutzer wird nach der Autorisierung durch Spotify zur Weiterleitung verarbeitet. Der Token wird in der Sitzung gespeichert. '''
    try:
        print("REDIRECT SUCCESS")
        sp_oauth = create_spotify_oauth()
        code = request.args.get('code')
        if not code:
            return apology("Spotify authorization code not provided.", 400)
        token_info = sp_oauth.get_cached_token()
        if not token_info:
            token_info = sp_oauth.get_access_token(code)
            print("Failed to retrieve access token.", 400)
            return redirect("/")

        session[TOKEN_INFO] = token_info  # Speichern Sie das Token in der Sitzung

        return redirect(url_for('index', _external=True)) # return redirect(url_for('get_current_track', _external=True))
    except Exception as e:
        print("REDIRECT FAILURE")
        flash("Internal Error, Wait (1-2min) and Restart!")
        return redirect("/login")


@app.route("/save_genre_colors", methods=["POST"])
@login_required
def save_genre_colors():
    '''Speichert Genre Farbe in DB'''
    user_id = session["user_id"]

    for genre in request.form:
        color = request.form.get(genre)
        genre_name = genre.split('_', 1)[1]  # Extrahiere den Genre-Namen
        color_oder = request.form.get(f'color_oder_{genre_name}', '#FFFFFF')
        # Überprüfen, ob das Genre bereits existiert
        existing_genre = db.execute("SELECT * FROM genre_colors WHERE genre = ? AND user_id = ?",genre_name, user_id)

        if existing_genre:
            # Aktualisiere die Farbe, wenn das Genre bereits existiert
            db.execute("UPDATE genre_colors SET color = ? WHERE genre = ? AND user_id = ?",color, genre_name, user_id
            )
        else:
            db.execute("INSERT INTO genre_colors (genre, color, user_id) VALUES (?, ?, ?)",genre_name, color, user_id)

    return redirect("/")  # Zurück zur Hauptseite oder zu einer anderen Seite

@app.route("/pause", methods=["POST"])
@login_required
def pause():
    user_id = session["user_id"]
    pause = request.form.get("pause")

    try:
        token_info = get_token()
        sp = spotipy.Spotify(auth=token_info['access_token'])

        # Check if the user has an active device
        devices = sp.devices()
        active_device = next((device for device in devices['devices'] if device['is_active']), None)

        if not active_device:
            print("No active device found. Please open Spotify and try again.")
            return redirect(url_for('index'))

        # Pause or resume playback
        if pause:
            check_pause(user_id, 1)
            sp.start_playback(device_id=active_device['id'])
            #flash("Song paused", "success")
        else:
            check_pause(user_id, 0)
            sp.pause_playback(device_id=active_device['id'])
            #flash("Song resumed", "success")

        return redirect(url_for('index'))

    except spotipy.exceptions.SpotifyException as e:
        flash(f"PAUSE ERROR: {str(e)}")
        return redirect(url_for('index'))

@app.route("/skip_track", methods=["POST"])
@login_required
def skip_track():
    try:
        token_info = get_token()
        sp = spotipy.Spotify(auth=token_info['access_token'])
        sp.next_track()
        return redirect("/")

    except Exception as e:
        flash(f"Skip ERROR: {str(e)}")
        return redirect(url_for('index'))

@app.route("/prev_track", methods=["POST"])
@login_required
def prev_track():
    try:
        token_info = get_token()
        sp = spotipy.Spotify(auth=token_info['access_token'])
        sp.previous_track()
        return redirect("/")

    except Exception as e:
        print(f"Error Skipping Song: {e}")

def spotify_login():
    sp_oauth = create_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

def get_current_track():
    ''' Sucht spielendes Lied & Artist und benutzt itunes API fürs Genre'''
    try:
        token_info = get_token()  # Token abrufen
        print(f"GET CURRENT TRACK token: {token_info}")
        sp = spotipy.Spotify(auth=token_info['access_token'])  # Spotify-Objekt erstellen
        current_track = sp.current_user_playing_track()
        if current_track["is_playing"]:
            # Lied wird abgespielt
            check_pause(session["user_id"], 1)
        else:
            # Lied ist pausiert.
            check_pause(session["user_id"], 0)

        if not current_track: # and not current_track["item"]:
            return {"track_name": "No track playing", "artist_name": "No artist", "Genre": "Not Found"}

        track_name = current_track["item"]["name"]
        artist_name = current_track["item"]["artists"][0]["name"]
        primary_genre_name = "Not Found"
        cover_url = "Not Found"

        try:
            search_query = quote(f"{track_name} {artist_name}")
            response = requests.get(f"https://itunes.apple.com/search?entity=song&limit=1&term={search_query}").json()
            results = response.get("results", [])
            primary_genre_name = "Not Found"
            if results:
                primary_genre_name = results[0].get("primaryGenreName", "Not Found")

        except Exception as e:
            print(f"Error fetching genre from iTunes: {e}")

        try:
            album_info = current_track["item"]["album"]
            cover_url = album_info["images"][0]["url"]  # Das erste Bild ist normalerweise das größte
        except Exception as e:
            print(f"Error fetching cover URL from Spotify: {e}")


        return {"track_name": track_name, "artist_name": artist_name, "genre": primary_genre_name, "cover_url": cover_url}

    except Exception as e:
        print(f"Error getting current track: {str(e)}")
        return {"track_name": "Not Found", "artist_name": "Not Found", "genre": "Not Found", "cover_url": "Not Found"}


def save_current_track(track_info, user_id):
    ''' Speichert aktuelles Lied, Künstler und Genre in DB'''
    try:
        existing_track = db.execute("SELECT id FROM tracks WHERE user_id = ? AND track_name = ? AND artist_name = ?", user_id, track_info["track_name"], track_info["artist_name"])
        if existing_track:
            return
        db.execute("INSERT INTO tracks (user_id, track_name, artist_name, genre) VALUES (?, ?, ?, ?)", user_id, track_info["track_name"], track_info["artist_name"], track_info["genre"])
    except Exception as e:
        # Fehlerbehandlung
        print(f"Error saving genre: {e}")

    try:
        existing_genre = db.execute("SELECT id FROM genre_colors WHERE genre = ? AND user_id = ?", track_info["genre"], user_id)
        if existing_genre:
            return
        db.execute("INSERT INTO genre_colors (genre, color, user_id) VALUES (?, ?, ?)", track_info["genre"], "#787878", user_id)
    except Exception as e:
        return apology(f"Error saving current track: {str(e)}", 500)


def get_genres_for_user(user_id):
    try:
        genres = db.execute("SELECT DISTINCT genre FROM tracks WHERE user_id = ?", user_id)
        return {"genres": [row["genre"] for row in genres if row["genre"]]}
    except Exception as e:
        return {"genres": []}

def get_genre_colors_for_user(user_id):
    """ Holt die Genre-Farben für den aktuellen Benutzer aus der Datenbank """
    genres = db.execute("SELECT genre, color FROM genre_colors WHERE user_id = ?", user_id)
    return {row["genre"]: row["color"] for row in genres}


def update_led_color(track_info, user_id, device):
    ''' Passt LED Farbe mit Genre an'''
    genre = track_info.get("genre")
    color = db.execute("SELECT color FROM genre_colors WHERE genre = ? AND user_id = ?", genre, user_id)

    if not color or not genre:
        return

    # Konvertiere Hex in HSV
    h, s, v = hex_to_hsv(color[-1]['color']) # Nimm das letzte Element der Liste

    tinytuya_config = {
        "apiKey": device[0]["TUYA_ACCESS_ID"],
        "apiSecret": device[0]["TUYA_ACCESS_KEY"],
        "apiRegion": "eu-w",
        "apiDeviceID": device[0]["DEVICE_ID"]
    }

    try:
        with open("../tinytuya.json", "w") as json_file:
            json.dump(tinytuya_config, json_file, indent=4)
    except Exception as e:
        return

    try:
        tuya_cloud = tinytuya.Cloud(apiRegion="eu-w", apiKey=device[0]["TUYA_ACCESS_ID"], apiSecret=device[0]["TUYA_ACCESS_KEY"])
    except Exception as e:
        return

    commands = {"commands": [{"code": "colour_data",
                              "value": {"h": h, "s": s, "v": v}}]}
    try:
        tuya_cloud.sendcommand(device[0]["DEVICE_ID"], commands)
        return redirect("/")
    except Exception as e:
        return

def hex_to_hsv(hex_color):
    hex_color = hex_color.lstrip("#")
    r, g, b = [int(hex_color[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]

    h, s, v = colorsys.rgb_to_hsv(r, g, b)

    # Skaliere die Werte nach den Anforderungen von Tuya
    h = int(h * 360)  # Hue in [0, 360]
    s = 1000  # Saturation in [0, 1000]
    v = 1000  # Value in [0, 1000]
    return h, s, v

# Funktion, um HEX in HSV umzuwandeln und den Hue-Wert (H) zurückzugeben
def hex_to_hue(hex_color):
    # HEX in RGB umwandeln
    hex_color = hex_color.lstrip("#")
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    # RGB in den Bereich [0, 1] normalisieren
    r, g, b = r / 255, g / 255, b / 255
    # Min und Max finden
    cmax, cmin = max(r, g, b), min(r, g, b)
    delta = cmax - cmin
    # Hue berechnen
    if delta == 0:
        hue = 0
    elif cmax == r:
        hue = (60 * ((g - b) / delta) + 360) % 360
    elif cmax == g:
        hue = (60 * ((b - r) / delta) + 120) % 360
    else:
        hue = (60 * ((r - g) / delta) + 240) % 360
    return hue

def reorder_colors(user_id):
    # Abrufen der Farbwerte aus der Datenbank
    colors = db.execute("SELECT id, color, genre FROM genre_colors WHERE user_id=?", user_id)

    # Funktion, um HEX in HSV umzuwandeln und den Hue-Wert (H) zurückzugeben

    # Liste der Farben mit ihren Hue-Werten erstellen
    color_hues = [
        {"id": row["id"], "genre": row["genre"], "color": row["color"], "hue": hex_to_hue(row["color"])}
        for row in colors
    ]

    # Farben basierend auf dem Hue-Wert sortieren
    sorted_colors = sorted(color_hues, key=lambda x: x["hue"])

    # Neue Reihenfolge in der Datenbank speichern
    for order, color in enumerate(sorted_colors, start=1):
        db.execute("UPDATE genre_colors SET color_order=? WHERE id=?", order, color["id"])

    # Abfrage der Genres und Farben in der neuen Reihenfolge
    genres = db.execute("SELECT genre, color FROM genre_colors WHERE user_id = ? ORDER BY color_order", user_id)

    # Ergebnisse vorbereiten
    genre_colors = {row["genre"]: row["color"] for row in genres}  # Farben als Dictionary
    sorted_genres = {"genres": [row["genre"] for row in genres]}   # Genres als Liste

    return genre_colors, sorted_genres

def stats(user_id):
    try:
        top_artists = db.execute("SELECT artist_name, COUNT (*) AS play_count FROM tracks WHERE user_id=? GROUP BY artist_name ORDER BY play_count DESC LIMIT 3", user_id)
        top_genres = db.execute("SELECT genre, COUNT(*) AS genre_count FROM tracks WHERE user_id=? GROUP BY genre ORDER BY genre_count DESC LIMIT 5",user_id)

    except Exception as e:
        return apology("Internal Error with DB Stats", 500)

    return {
        'top_artists': top_artists,
        'top_genres': top_genres
    }

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return int(hex_color[:2], 16), int(hex_color[2:4], 16), int(hex_color[4:], 16)

def rgb_to_pastel(rgb_color):
    return tuple(int((value + 255) / 2) for value in rgb_color)

def rgb_to_hex(rgb_color):
    return "#{:02x}{:02x}{:02x}".format(rgb_color[0], rgb_color[1], rgb_color[2])

def convert_to_pastel(genre_colors):
    pastel_colors = {}
    for genre, color in genre_colors.items():
        rgb = hex_to_rgb(color)  # Hex zu RGB
        pastel_rgb = rgb_to_pastel(rgb)  # RGB zu Pastell-RGB
        pastel_hex = rgb_to_hex(pastel_rgb)  # RGB zu Hex
        pastel_colors[genre] = pastel_hex  # Speichere das Ergebnis
    return pastel_colors


def genre_plot(user_id,pastel_colors):
    try:
        genre_data = db.execute(
            "SELECT genre, COUNT(*) AS genre_count FROM tracks WHERE user_id=? GROUP BY genre ORDER BY genre_count DESC",user_id)

        # Sortieren und Plot-Daten extrahieren
        df = pd.DataFrame(genre_data).sort_values(by='genre_count', ascending=True)

        # Hinzufügen der Farben basierend auf den Pastellfarben
        df['color'] = df['genre'].apply(
            lambda genre: pastel_colors.get(genre, '#FFF'))  # Standardfarbe für nicht definierte Genres

        # Gruppieren nach Farbe
        grouped = df.groupby('color').agg({'genre_count': 'sum', 'genre': 'count'}).reset_index()

        # Sortieren der Gruppen nach der Gesamtzahl der Plays
        grouped_sorted = grouped.sort_values(by='genre_count', ascending=True)

        # Plot erstellen
        fig, ax = plt.subplots(figsize=(5, 5))  # Kompaktere Plot-Größe
        group_colors = grouped_sorted['color'].tolist()  # Farbzuweisung
        group_counts = grouped_sorted['genre_count'].tolist()  # Gesamtzahl der Plays für jede Farbgruppe
        ax.pie(group_counts, startangle=90, colors=group_colors)

        # Plot in Base64-String konvertieren
        buffer = io.BytesIO()
        plt.savefig(buffer, format="png", transparent=True)
        buffer.seek(0)
        return base64.b64encode(buffer.read()).decode('utf-8')

    except Exception as e:
        print(f"Error generating genre plot: {e}")
        return None


def get_user_info(token):
    print(f"GET USER INFO TOKEN {token}")
    url = "https://api.spotify.com/v1/me"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    response = requests.get(url, headers=headers)
    print(f"response: {response}")
    print(f"headers: {headers}")

    if response.status_code == 200:
        user_info = response.json()
        return user_info  # Gibt Benutzerinformationen zurück, wie z.B. die Spotify-ID, den Namen usw.

    else:
        raise Exception(f"Fehler beim Abrufen der Benutzerinformationen: {response.status_code}")

def delete_folders():
    folders_to_delete = ["flask_session", ".cache"]
    try:
        for folder in folders_to_delete:
            folder_path = os.path.join(os.getcwd(), folder)
            if os.path.exists(folder_path):
                print(f"Der Ordner '{folder_path}' existiert.")
            else:
                print(f"Der Ordner '{folder_path}' existiert nicht oder ist ungültig.")

            for root, dirs, files in os.walk(folder_path, topdown=False):
                for file in files:
                    os.remove(os.path.join(root, file))
                for dir in dirs:
                    os.rmdir(os.path.join(root, dir))
            os.rmdir(folder_path)
            print(f"{folder} wurde gelöscht.")
        else:
            print(f"{folder} existiert nicht.")

    except Exception as e:
        print(f"Error deleting folders {e}")

def clear_spotify_cache():
    cache_path = os.path.join(os.getcwd(), ".cache")
    if os.path.exists(cache_path):
        os.remove(cache_path)  # Löscht die Cache-Datei
        print(".cache wurde erfolgreich gelöscht.")
    else:
        print(".cache fehler beim löschen")

# Rufe diese Funktion auf, wenn der Cache nach der Nutzung gelöscht werden soll


if __name__ == "__main__":
    app.run(debug=True)
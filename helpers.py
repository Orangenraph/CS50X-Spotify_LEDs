from flask import redirect, render_template, session
from functools import wraps
from cs50 import SQL

import os
import tinytuya

# {"access_token": "BQAvJhW_rmNFME7Bj3Ixsj6QsoHghRVO9vTcDnWGEXsrXdtaEd0Grrjg404Ol7VEfs_6LnwN9oOce0Q16eoGjMtAQGyiJuoJgWvovmWytb445VEx_0YJJ4g1rI4-oP1Rc6kdo09RYhBryfN8KkKOqAIV3QfRXj5PnfQ65FZatSZczbRULkojWS_6t1ag018tL7Uxh3fr9oZq58dyRFI6AXgL7pClLnKeJmTr", "token_type": "Bearer", "expires_in": 3600, "scope": "user-read-playback-state user-modify-playback-state user-read-currently-playing user-top-read", "expires_at": 1734718874, "refresh_token": "AQAXtgM8YTEV7rXaSPTWpSCohYxf7T2Sz41xAa8pn1EVYwc7YK3v4kyn2wTLzDKYZw4fCtgUlKseAmV7Ir5LfVaeqIdqs_4LprpwZXQLMvqUE5q6n5a11HT6J73EEqCt2Gk"}
# {"access_token": "BQD3_PiqHkG5ofptRttbaVEMVl1ISrfUWzvfvWZFxTjEIaD8BsQ6-vSqAvD59ASxN26XpQaoTtsZAI9xcfNfIl7JHQ9g6OwX_iww8BoWk_B_t1Br4Gq1tiVBtz0k-lWmcOnZBZNz0KKRgpFPzrdSHy8VnHXU8AHiMhr_Ib7Inq-M4dr7okCl-QanUDMGK0QcwKVk4EEVlxHIAxgH2cUI5HmHTpZ0", "token_type": "Bearer", "expires_in": 3600, "refresh_token": "AQBEDeQcHM2w30NyKWB05ZDxlQQYk4Mfjvgh3sDUtAgCYClSgcqmzO_EhW7B2mRLcAO1lTe_vefsu2zjptlhdxQ0-7SaT5ukeaQwZn2P7xH1jTPQXQyKYQZPX6enMzTbxdM", "scope": "user-read-playback-state user-modify-playback-state user-read-currently-playing user-top-read", "expires_at": 1734738641}

def apology(message, code=400):
    """Render message as an apology to user."""

    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [
            ("-", "--"),
            (" ", "-"),
            ("_", "__"),
            ("?", "~q"),
            ("%", "~p"),
            ("#", "~h"),
            ("/", "~s"),
            ('"', "''"),
        ]:
            s = s.replace(old, new)
        return s

    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/latest/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function

def device_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get("user_id")
        db = SQL("sqlite:///SQLite")


        # Überprüfen, ob der Benutzer eingeloggt ist und ein Gerät hat
        if user_id is None:
            return redirect("/login")  # Umleitung zur Login-Seite, falls nicht eingeloggt

        # Überprüfen, ob der Benutzer ein registriertes Gerät hat
        device = db.execute("SELECT * FROM device WHERE user_id = ?", user_id)

        if not device:  # Falls kein Gerät registriert ist
            return redirect("/device")  # Umleitung zur Seite zum Hinzufügen eines Geräts

        return f(*args, **kwargs)

    return decorated_function











def connect_tuya():
    tuya_api_endpoint = os.getenv('https://openapi-weaz.tuyaeu.com')
    tuya_access_id = os.getenv('rxkhtwfewwhck3r47kgq')
    tuya_access_key = os.getenv('fb278b8bf87e4dfba24a5ae5b3b70469')

    DEVICE_ID = '9ba70c86fd24fbe4721del'

    # Connecto to Tuya API
    tuya_cloud = tinytuya.Cloud(apiRegion=tuya_api_endpoint, apiKey=tuya_access_id, apiSecret=tuya_access_key)

    # API_ENDPOINT: cn, us, us-e, eu, eu-w, or in. Options based on tinytuya python library
    commands = {
        "commands": [
            {"code": "switch_led", "value": False},
        ]
    }

    tuya_cloud.sendcommand(DEVICE_ID, commands)

connect_tuya()

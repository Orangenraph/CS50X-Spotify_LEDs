from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, login_required


app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False # Sitzung schließt nach Browsers löschen
app.config["SESSION_TYPE"] = "filesystem" # Speichert Sitzungsdaten als temporäre Dateien auf dem Server (anstelle von Cookies)
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

@app.route("/")
@login_required
def index():
    return render_template("index.html")


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

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

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

@app.route("/settings")
def settings():
    return render_template("settings.html")






if __name__ == "__main__":
    app.run(debug=True)
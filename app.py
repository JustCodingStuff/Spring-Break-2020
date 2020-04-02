from flask import Flask, redirect, url_for, render_template, request, session, flash, send_file
from datetime import timedelta
from flask_sqlalchemy import SQLAlchemy
import requests
from bs4 import BeautifulSoup
import os

youtube_base_url = "https://www.youtube.com/results?search_query= {}"

app = Flask(__name__)
app.secret_key = "hello"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.sqlite3'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120))
    password = db.Column(db.String(30))

    def __init__(self, email, password):
        self.email = email
        self.password = password


@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        session.permanent = True
        email = request.form["loginEmail"]
        password = request.form["loginPassword"]
        session["email"] = email
        session["password"] = password
        found_user = User.query.filter_by(email=email).first()
        if found_user:
            if found_user.password == password:
                return redirect(url_for("songDownloader"))
            else:
                flash("The password entered is incorrect.")
        else:
            flash("This email is not connected to an account.")
    return render_template("login.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        found_user = User.query.filter_by(email=email).first()
        if not found_user:
            usr = User(email=email, password=password)
            db.session.add(usr)
            db.session.commit()
        else:
            flash("An account with this email already exists. Please Login.")
        return redirect(url_for("login"))
    else:
        return render_template("signup.html")


@app.route("/download", methods=["GET", "POST"])
def songDownloader():
    if request.method == "POST":
        songName = request.form["songName"]

        search_url = youtube_base_url.format(str(songName))
        r = requests.get(search_url)
        soup = BeautifulSoup(r.text, "html.parser")
        unique_search_href = ""
        for vid in soup.findAll(attrs={'class': 'yt-uix-tile-link'}, limit=1):
            unique_search_href = vid["href"]
        song_url = f"https://www.youtube.com{unique_search_href}"

        try:
            os.system(f"youtube-dl --extract-audio --audio-format mp3 -o  '{songName}.mp3' {song_url}")
            flash("Song Download Successful!")
        except:
            flash("Download Unsuccessful")

    return render_template("songDownloader.html")


if __name__ == "__main__":
    db.create_all()
    app.run(debug=True)

# "#" in CSS is id
# "." in CSS is class

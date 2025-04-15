from flask import Flask, render_template, request, url_for, session, redirect
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

import math
import os

NAME = "name"
ROUTE = "route"
USER = "username"
PERMISSION = "permission"

app = Flask(__name__)

# Konfigurace SQLite databáze
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

@app.before_request
def create_db():
    if not hasattr(app, 'db_initialized'):
        db.create_all()
        app.db_initialized = True  # Zamezení opakovaného vytváření tabulek

app.secret_key = "kilcek"

def get_gallery():
    dirlist = os.listdir("static/gallery")
    dirlist.remove("Thumbs.db")
    return dirlist


@app.route("/")
def home():
    return render_template("home.html", title = "Home")

def return_tools():
    return[
        {NAME:"Domů", ROUTE:"/"},
        {NAME:"Mocniny", ROUTE:"/mocnina"},
        {NAME:"Články", ROUTE:"/clanky"},
        {NAME:"Galerie", ROUTE:"/gallery"},
        {NAME:"Ovládání databází",ROUTE:"/db_control"},
        {NAME:"Videoteka", ROUTE:"/films"}
    ]

@app.route("/register",methods=["POST","GET"])
def register():
    error = 0
    if request.method == "POST":
        
        username = request.form["username"]
        paswd1 = request.form["password1"]
        paswd2 = request.form["password2"]
        f = open("uzivatel","r")
        if paswd1 != paswd2:
            error = 2
        elif username in f.read():
            error = 1
        f.close()
        if error == 0:
            with open("uzivatel", "a") as file:
                file.write(username)
                file.write(";")
                file.write(generate_password_hash(paswd1)+"\n")
                file.close()

            session["uzivatel"] = username
            return render_template("home.html")


    return render_template("register.html", title = "Registrace", error=error)



@app.route("/logout")
def logout():
    del session[NAME]
    del session[PERMISSION]
    return redirect("/")

@app.route("/login",methods=["POST","GET"])
def login():
    session[USER] = "admin"
    session[PERMISSION] = True
    return redirect("/")
    
    if request.method == "POST":
        valid = 0
        if request.method == "POST":
            name = request.form["username"]
            password = request.form["password"]
            
            with open("uzivatel","r") as file:
                for record in file:
                    seznam = record.split(";")
                    encryptet = seznam[1].replace("\n","")
                    if name == seznam[0] and check_password_hash(encryptet, password):
                        session["uzivatel"] = name
                        valid = 0
                        break
                    else:
                        valid = 1
        if valid:
            return render_template("login.html", title = "Login", valid = valid)
        else:
            return render_template("index.html", title = "Home")
    return render_template("login.html", title = "Login")

@app.route("/films")
def films():
    sqlreq = db.session.execute(text('SELECT * FROM film'))
    movies = sqlreq.fetchall()

    return render_template("films.html", title="Filmy", tools=return_tools(), movies=movies)

@app.route("/films/add", methods = ['POST'])
def add_film():
    if request.method == "POST":
        title = request.form.get('title')
        desc = request.form.get("desc")
        year = request.form.get('year')

        db.session.execute(text(f"INSERT INTO film(title, description, release_year, language_id, last_update) VALUES ('{title}', '{desc}', {year}, 1, datetime())"))
        db.session.commit()

        return films()

@app.route("/films/pop")
def pop_film():

    db.session.execute(text('DELETE FROM film WHERE film_id = 1002'))
    db.session.commit()
    return films()


@app.route("/public_archive")
def public_arch():
    return render_template("public.html")

@app.route("/record/<int:a>")
def record(a):
    return render_template("record.html")

@app.route("/about")
def about():
    return render_template("about.html")



@app.route("/gallery")
def gallery():
    files = os.listdir("static/gallery")
    #files.pop()
    return render_template("gallery.html", title="Galerie", tools=return_tools(), file=get_gallery(), state=-1)

@app.route("/gallery/upload", methods=["POST"])
def upload():

    if request.method == "POST":
        try:
            f = request.files["soubor"]
            f.save("static/gallery/"+f.filename)
            state = 0
        except:
            state = 1

    files = os.listdir("static/gallery")
    #files.pop()
    return render_template("gallery.html", title="Galerie", tools=return_tools(), file=get_gallery(), state=state)




if __name__ == "__main__":
    app.run(debug=True, port=8080)

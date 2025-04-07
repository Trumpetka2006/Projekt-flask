from flask import Flask, render_template, request, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

import math
import os

NAME = "name"
ROUTE = "route"
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


    return render_template("signin.html", title = "Registrace", error=error)



@app.route("/loguot")
def loguot():
    del session["uzivatel"]
    return render_template("status.html", title="Stav", tools=return_tools())

@app.route("/login",methods=["POST","GET"])
def login():
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


@app.route("/db_control")
def control_panel():
    return render_template("db_control.html", title="Ovádání databází", tools=return_tools())

@app.route("/db_control/state")
def db_state():
    sqlreq = db.session.execute(text('SELECT * FROM film'))
    actors = sqlreq.fetchall()

    return render_template("db_control.html", title="Ovádání databází", tools=return_tools(), output=actors)

@app.route("/db_control/film_actors")
def actors():
    sqlreq = db.session.execute(text("""
                                        SELECT actor.actor_id, actor.first_name, actor.last_name FROM actor 
                                        JOIN film_actor ON actor.actor_id = film_actor.actor_id 
                                        JOIN film ON film_actor.film_id = film.film_id
                                        GROUP BY actor.actor_id
                                     """))
    actors = sqlreq.fetchall()

    sqlreq = db.session.execute(text("""
                                        SELECT actor.actor_id, film.title FROM actor
                                        JOIN film_actor ON actor.actor_id = film_actor.actor_id 
                                        JOIN film ON film_actor.film_id = film.film_id
                                    """))
    films = sqlreq.fetchall()

    result = []
    for actor in actors:
        cast = []
        for film in films:
            if actor[0] == film[0]:
                cast.append(film[1])
        result.append((f"{actor[1]} {actor[2]}", cast))

    return render_template("db_control.html", title="Ovádání databází", tools=return_tools(), output=result)

@app.route("/db_control/add_user",methods=["POST"])
def add_user():
    if request.method == "POST":
        id = request.form["id"]
        name = request.form["username"]
        password = request.form["password"]

    return render_template("db_control.html", title="Ovádání databází", tools=return_tools(), output=">")
    

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

@app.route("/clanky")
def clanky():
    clanky = vrat_clanky()
    return render_template("clanky.html", articles=clanky, tools = return_tools(), title="Články")

def vrat_clanky():
    return [
        {"nadpis": "První Článek","author":"Pavel", "text": "Toto je text članku."},
        {"nadpis": "Druhy Článek","author":"Pavel", "text": "Toto je text članku."},
        {"nadpis": "Třetí Článek","author":"Pavel", "text": "Toto je text članku."}
    ]
@app.route("/mocnina")
def mocnina():
    return render_template("vypocet.html", tools = return_tools(), title="Mocniny")

@app.route("/vypocet", methods=["POST"])
def vypocet():
    try:
        a = request.form["a"]
        x = request.form["x"]
        moc = int(a) ** int(x)
    except:
        return "kokote!"
    return render_template("vypocet.html", data=moc, tools = return_tools(), title="Mocniny")


""" @app.route("/mocnina/<int:a>/<int:b>")
@app.route("/mocnina/<float:a>/<float:b>")
def mocnina(a, b):
    return f"{a} na {b} je {a**b}" """


@app.route("/sqr/<int:a>")
@app.route("/sqr/<float:a>")
def sqroot(a):
    return f"druhá odmocnina čisla {a} je {math.sqrt(a)}"


if __name__ == "__main__":
    app.run(debug=True, port=8080)

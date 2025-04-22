from flask import Flask, render_template, request, url_for, session, redirect
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

import math
import os

NAME = "name"
ROUTE = "route"
USER = "username"
ID = "id"
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
        email = request.form["email"]
        if paswd1 != paswd2:
            error = 2
        req = db.session.execute(text("SELECT users.name FROM users"))
        users = req.fetchall()
        for user in users:
            if user[0] == username:
                error = 1

        if error == 0:
            print(username)
            print(generate_password_hash(paswd1))
            pashash = generate_password_hash(paswd1)
            db.session.execute(text(f"INSERT INTO users (name, email, password, is_employee, registration_date) VALUES ('{username}', '{email}', '{pashash}', 0, date())"))
            db.session.commit()

            session[USER] = username
            session[PERMISSION] = False
            return render_template("home.html")


    return render_template("register.html", title = "Registrace", error=error)



@app.route("/logout")
def logout():
    del session[USER]
    del session[PERMISSION]
    return redirect("/")

@app.route("/login",methods=["POST","GET"])
def login():
    if request.method == "POST":
        name = request.form["username"]
        password = request.form["password"]

        req = db.session.execute(text(f"SELECT users.password FROM users WHERE name == '{name}'"))
        passhash = req.fetchall()
        
        try:
            if check_password_hash(passhash[0][0], password):
                req = db.session.execute(text(f"SELECT users.is_employee FROM users WHERE name == '{name}'"))
                data = req.fetchall()
                session[USER] = name
                session[PERMISSION] = data[0][0]
                return redirect("/")
            else:
                return render_template("login.html", title = "Login", valid = True)
        except IndexError:
                return render_template("login.html", title = "Login", valid = False)
    return render_template("login.html")

@app.route("/add-record", methods = ["POST", "GET"])
def add_record():
    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]
        target = request.form["target"]

        req = db.session.execute(text(f"SELECT users.id FROM users WHERE name == '{session[USER]}'"))
        id = req.fetchall()[0][0]
        
        db.session.execute(text(f"INSERT INTO {target} (title, content, autor_id, cration_date) VALUES ('{title}','{content}',{id},date())"))
        db.session.commit()
        return redirect("/public_archive")
    return render_template("add-record.html")

@app.route("/del-record/<int:a>")
def del_record(a):
    if session[USER] == "admin":
        db.session.execute(text(f"DELETE FROM public WHERE id = {a}"))
        db.session.commit()
    return redirect("/public_archive")

@app.route("/account", methods = ['POST', 'GET'])
def account():
    if request.method == "POST":
        old = request.form['old']
        new = request.form['new']
        again = request.form['again']
        req = db.session.execute(text(f"SELECT password FROM users WHERE name == '{session[USER]}'"))
        old_hash = req.fetchall()[0][0]

        if check_password_hash(old_hash, old):
            print("Staré heslo se shoduje")
            if new == again:
                print("Hesla se shodují")
                db.session.execute(text(f"UPDATE users SET password = '{generate_password_hash(new)}' WHERE name = '{session[USER]}'"))
                db.session.commit()
                return redirect("/")

    req = db.session.execute(text(f"SELECT name, email, registration_date FROM users WHERE name == '{session[USER]}'"))
    return render_template("account.html", info = req.fetchall()[0])


@app.route("/public_archive")
def public_arch():
    req = db.session.execute(text("SELECT public.id, public.title, users.name, public.cration_date FROM public JOIN users on public.autor_id = users.id ORDER BY public.id DESC"))
    return render_template("public.html", records = req.fetchall())

@app.route("/record/<int:a>")
def record(a):
    req = db.session.execute(text(f"SELECT public.title, public.content , users.name, public.cration_date, public.id FROM public JOIN users on public.autor_id = users.id WHERE public.id = {a}"))
    return render_template("record.html", content=req.fetchall()[0])

@app.route("/about")
def about():
    return render_template("about.html")



if __name__ == "__main__":
    app.run(debug=True, port=8080)

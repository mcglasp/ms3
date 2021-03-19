import os
from flask import (
    Flask, flash, render_template, 
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env


app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)


@app.route("/")
@app.route("/get_terms", methods=["GET"])
def get_terms():
    terms = list(mongo.db.terms.find())
    incorrect_terms = list(mongo.db.terms.incorrect_terms.find())

    return render_template("get_terms.html", terms=terms, incorrect_terms=incorrect_terms)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Check if username already exists
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            flash("Username already exists")
            return redirect(url_for("register"))

        register = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password"))
        }
        mongo.db.users.insert_one(register)
        
        # Put the new user into 'session' cookie
        session["user"] = request.form.get("username").lower()
        flash("Registration successful")
        return redirect(url_for("profile", username=session["user"]))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # check if username exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            # ensure hashed password matches user input
            if check_password_hash(existing_user["password"], request.form.get("password")):
                session["user"] = request.form.get("username").lower()
                flash("Welcome, {}".format(request.form.get("username")))
                return redirect(url_for(
                    "profile", username=session["user"]))

            else:
                # invalid password match
                flash("Incorrect Username and/or Password")
                return redirect(url_for("login"))

        else:
            # username doesn't exist
            flash("Incorrect Username and/or Password")
            return redirect(url_for('login'))

    return render_template("login.html")


@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    # grab session user's username from db
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]

    if session["user"]:
        return render_template("profile.html", username=username)

    return redirect(url_for("login"))


@app.route("/logout")
def logout():
    # remove user from session cookies
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("login"))





@app.route("/add_term", methods=["GET", "POST"])
def add_term():
    # THESE IF STATEMENTS NEED DRYING!
    if request.form.get("incorrect_terms"):
        to_split = request.form.get("incorrect_terms")
        to_split.strip(",")
        # ADD REGEX TO PROPERLY FORMAT INPUTS
        split_inc_terms = to_split.split(" ")

    if request.form.get("alt_terms"):
        to_split = request.form.get("alt_terms")
        to_split.strip(",")
        # ADD REGEX TO PROPERLY FORMAT INPUTS
        split_alt_terms = to_split.split(" ")
        
    if request.method == "POST":
        term = {
            "term_name": request.form.get("term_name"),
            "alt_terms": split_alt_terms,
            "incorrect_terms": split_inc_terms,
            "usage_notes": request.form.get("usage_notes"),
            "type_name": request.form.get("type_name")
            }

        mongo.db.terms.insert_one(term)
        flash("Term added")
        return redirect(url_for("add_term"))
    
    types = mongo.db.types.find().sort("types", 1)
    return render_template("add_term.html", types=types)


@app.route("/manage_users")
def manage_users():
    users = list(mongo.db.users.find())
    
    return render_template("manage_users.html", users=users)

if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)
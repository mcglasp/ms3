import os
from datetime import datetime
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
@app.route("/get_terms")
def get_terms():
    terms = list(mongo.db.terms.find())
    incorrect_terms = list(mongo.db.terms.incorrect_terms.find())

    return render_template("get_terms.html", terms=terms, incorrect_terms=incorrect_terms)


@app.route("/manage_term/<term_id>", methods=["GET", "POST"])
def manage_term(term_id):
    user = session['user']
    access_level = mongo.db.users.find_one({"username": session['user']})['access_level']
    term = mongo.db.terms.find_one({"_id": ObjectId(term_id)})
    comments = list(mongo.db.comments.find())
    term_comments = mongo.db.comments.find({"rel_term_id": ObjectId(term_id)})

    return render_template("manage_term.html", term=term, term_comments=term_comments, user=user, comments=comments, access_level=access_level)


@app.route("/add_comment/<term_id>", methods=["GET", "POST"])
def add_comment(term_id):
    term = mongo.db.terms.find_one({"_id": ObjectId(term_id)})

    if request.method == "POST":
        now = datetime.now()
    
        comment = {
            "timestamp": now.strftime("%d/%m/%Y, %H:%M:%S"),
            "comment": request.form.get("comment"),
            "commenter": session['user'],
            "rel_term_id": term["_id"]
            }

        mongo.db.comments.insert_one(comment)
        flash("Hooray it worked!")
        return redirect(url_for("manage_term", term_id=term_id))


@app.route("/delete_comment/<comment_id>/<term_id>")
def delete_comment(comment_id, term_id):
    mongo.db.comments.remove({"_id": ObjectId(comment_id)})
    flash("Comment successfully deleted")
    return redirect(url_for("manage_term", term_id=term_id))


@app.route("/flag_comment/<comment_id>/<term_id>")
def flag_comment(comment_id, term_id):
    users = mongo.db["users"]
    username = users.find_one({"username": session["user"]})["username"]
    flagger = {"username": username}
    flagged_comment = {"$push": {"flagged_comments": comment_id}}
    comments = mongo.db["comments"]
    flag_query = {"_id": ObjectId(comment_id)}
    flagged_by = {"$push": {"flagged_by": username}}
    user_record_field = users.find({"$and": [{"username": username}, {"flagged_comments": comment_id}]}).count()
    
    if user_record_field > 0:
        flash("You have ALREADY flagged this comment")
        return redirect(url_for("manage_term", term_id=term_id, username=username))
    else:
        # push id to comment's 'flagged_by' array
        comments.update_one(flag_query, flagged_by)
        # push comment_id to user's 'flagged_comments' array
        users.update_one(flagger, flagged_comment)
        flash("You have flagged this comment")
        return redirect(url_for("manage_term", term_id=term_id, username=username))


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


@app.route("/choose_new_password", methods=["GET", "POST"])
def choose_new_password():
    user = mongo.db.users.find_one({"username": session["user"]})

    return render_template("choose_new_password.html", user=user)

@app.route("/change_password", methods=["GET", "POST"])
def change_password():
    user = mongo.db.users.find_one({"username": session["user"]})
    username = session["user"]
    password_one = request.form.get("new_password")
    password_two = request.form.get("confirm_password")

    if password_one == password_two:
        new_password = generate_password_hash(request.form.get("new_password"))

        if request.method == "POST":

            mongo.db.users.update({"username": username}, {"password": new_password})

            flash("Password updated")
            return redirect(url_for(
                    "profile", username=username))
            
        else:
            flash("Passwords do not match, please try again")
            return render_template('choose_new_password.html', username=username, user=user)


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
    user = mongo.db.users.find_one({"username": session["user"]})

    if session["user"]:
        return render_template("profile.html", user=user)

    return redirect(url_for("login"))


@app.route("/logout")
def logout():
    # remove user from session cookies
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("login"))


@app.route("/add_term", methods=["GET", "POST"])
def add_term():
    if request.method == "POST":
        alt = request.form.get("alt_terms")
        inc = request.form.get("incorrect_terms")

        class Term:

            def __init__(self, to_split):
                self.to_split = to_split

            def split_terms(self):
                request.form.get(self.to_split)
                return self.to_split.split(",")

        alt_split = Term(alt)
        alternatives = alt_split.split_terms()
        inc_split = Term(inc)
        incorrect = inc_split.split_terms()

        term = {
            "term_name": request.form.get("term_name"),
            "alt_terms": alternatives,
            "incorrect_terms": incorrect,
            "usage_notes": request.form.get("usage_notes"),
            "type_name": request.form.get("type_name")
            }

        mongo.db.terms.insert_one(term)
        flash("Term added")
        return redirect(url_for("add_term"))

    types = mongo.db.types.find().sort("types", 1)
    return render_template("add_term.html", types=types)


@app.route("/delete_term/<term_id>")
def delete_term(term_id):
    mongo.db.terms.remove({"_id": ObjectId(term_id)})

    flash("Term successfully deleted")
    return redirect(url_for("get_terms", term_id=term_id))


@app.route("/manage_users")
def manage_users():
    users = list(mongo.db.users.find())
    levels = mongo.db.access_levels.find().sort("level_name", 1)
    
    return render_template("manage_users.html", users=users, levels=levels)


@app.route("/add_user", methods=["GET", "POST"])
def add_user():
    if request.method == "POST":

        new_user = {
            "username": request.form.get("username"),
            "password": request.form.get("password"),
            "access_level": request.form.get("access_level")
        }

        mongo.db.users.insert_one(new_user)
        flash("New user added")
        return redirect(url_for("manage_users"))
    




if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)



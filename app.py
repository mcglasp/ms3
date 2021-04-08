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
    try:
        user = session['user']
        access_level = mongo.db.users.find_one({"username": user})['access_level'].lower()
        levels = list(mongo.db.access_levels.find())
        terms = list(mongo.db.terms.find())
        incorrect_terms = list(mongo.db.terms.incorrect_terms.find())
        alt_terms = list(mongo.db.terms.alt_terms.find())
        new_registrations = list(mongo.db.users.find({'access_level': 'requested'}))
        flagged_comments = mongo.db.comments.find().sort('timestamp', 1)
        timecol = mongo.db.comments.find({},{'_id':0,'timestamp':1})

        for x in timecol:
            y = x['timestamp']
            s = y.split(",")
            for t in s[0::2]:
                print(t)

        suggested_terms = mongo.db.terms.find({"pending": True})

        try:
            pinned_terms = list(mongo.db.users.find_one({"username": user})['pinned_terms'])
        except KeyError:
            pinned_terms = []
        else:
            pinned_terms = list(mongo.db.users.find_one({"username": user})['pinned_terms'])
        
        return render_template("get_terms.html", terms=terms, incorrect_terms=incorrect_terms, alt_terms=alt_terms, user=user, pinned_terms=pinned_terms, access_level=access_level, new_registrations=new_registrations, flagged_comments=flagged_comments, levels=levels, suggested_terms=suggested_terms)
    
    except KeyError:
        return redirect(url_for('login'))




    

@app.route("/view_term/<term_id>")
def view_term(term_id):
    user = session['user']
    access_level = mongo.db.users.find_one({"username": session['user']})['access_level']
    term = mongo.db.terms.find_one({"_id": ObjectId(term_id)})
    comments = list(mongo.db.comments.find())
    term_comments = mongo.db.comments.find({"rel_term_name": term["term_name"]})

    return render_template("view_term.html", term=term, term_comments=term_comments, user=user, comments=comments, access_level=access_level)


@app.route("/manage_term/<term_id>")
def manage_term(term_id):
    term = mongo.db.terms.find_one({"_id": ObjectId(term_id)})
    incorrect_terms = list(mongo.db.terms.incorrect_terms.find())
    alt_terms = list(mongo.db.terms.alt_terms.find())
    types = list(mongo.db.types.find())
    
    return render_template("manage_term.html", term=term, incorrect_terms=incorrect_terms, alt_terms=alt_terms, types=types)


@app.route("/pin_term/<term_id>")
def pin_term(term_id):
    term = mongo.db.terms.find_one({"_id": ObjectId(term_id)})
    term_name = term['term_name']
    users = mongo.db["users"]
    user = session['user']
    pinner = {"username": user}
    term_to_pin = {"$push": {"pinned_terms": term_name}}
    user_record_field = users.count_documents({"$and": [{"username": user}, {"pinned_terms": term_name}]})

    if user_record_field > 0:
        flash("Sorry, you've already pinned this term")
        return redirect(url_for("get_terms", user=user, term=term, term_name=term_name))
    else:        
        users.update_one(pinner, term_to_pin)
        flash("Term pinned to your dashboard")

    return redirect(url_for("get_terms", user=user, term=term, term_name=term_name))


@app.route("/remove_pin/<pinned>/<user>")
def remove_pin(pinned, user):
    user = session['user']
    mongo.db.users.update_one({"username": user}, {"$pull": {"pinned_terms": pinned}})
    
    flash("Pin successfully deleted")
    return redirect(url_for("get_terms", user=session['user']))


@app.route("/add_comment/<term_id>", methods=["GET", "POST"])
def add_comment(term_id):
    term = mongo.db.terms.find_one({"_id": ObjectId(term_id)})

    if request.method == "POST":
        now = datetime.now()
    
        comment = {
            "timestamp": now.strftime("%d/%m/%Y, %H:%M:%S"),
            'time': Timestamp,
            "comment": request.form.get("comment"),
            "user": session['user'],
            "rel_term_name": term['term_name']
            }
        print("gah")
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
            "password": generate_password_hash(request.form.get("password")),
            "access_level": "requested"
        }
        mongo.db.users.insert_one(register)
        
        # Put the new user into 'session' cookie
        session["user"] = request.form.get("username").lower()
        flash("Your registration request has been sent to the administrator")
        return redirect(url_for("register"))

    return render_template("register.html")


@app.route("/change_password", methods=["GET", "POST"])
def change_password():
    users = mongo.db["users"]
    existing_user = users.find_one(
        {"username": request.form.get("username").lower()}) 

    if request.method == "POST":
        new_password = request.form.get("new_password")

        if existing_user:
            if check_password_hash(existing_user["password"], request.form.get("password")):
                to_update = {"_id": existing_user["_id"]}
                updated_password = {"$set": {"password": generate_password_hash(new_password)}}
                users.update_one(to_update, updated_password)
                flash("Password successfully updated")
                return redirect(url_for(
                    "profile", username=session["user"]))

            else:
                # invalid password match
                flash("Incorrect Username and/or Current Password")
                return redirect(url_for("profile"))

        else:
            # username doesn't exist
            flash("Incorrect Username and/or Current Password")
            return redirect(url_for('profile'))

    return render_template("profile.html")


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
                    "get_terms", username=session["user"]))

            else:
                # invalid password match
                flash("Incorrect Username and/or Password")
                return redirect(url_for("login"))

        else:
            # username doesn't exist
            flash("Incorrect Username and/or Password")
            return redirect(url_for('login'))

    return render_template("login.html")


@app.route("/profile/<user>", methods=["GET", "POST"])
def profile(user):
    # grab session user's username from db
    user = session["user"]


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
    user = session['user']
    access_level = mongo.db.users.find_one({"username": user})['access_level']
    if request.method == "POST":
        
        alt = request.form.get("alt_terms")
        inc = request.form.get("incorrect_terms")

        class Term:

            def __init__(self, to_split):
                self.to_split = to_split

            def split_terms(self):
                request.form.get(self.to_split)
                split_len = len(self.to_split)
                if split_len > 0:
                    return self.to_split.split(",")
                else:
                    return []

        alt_split = Term(alt)
        alternatives = alt_split.split_terms()
        inc_split = Term(inc)
        incorrect = inc_split.split_terms()

        term = {
            "term_name": request.form.get("term_name"),
            "alt_terms": alternatives,
            "incorrect_terms": incorrect,
            "usage_notes": request.form.get("usage_notes"),
            "type_name": request.form.get("type_name"),
            "pending": False if access_level == 'administrator' else True,
            "created_by": session['user']
            }

        mongo.db.terms.insert_one(term)
        flash("Term added")
        return redirect(url_for("add_term"))

    types = mongo.db.types.find().sort("types", 1)
    return render_template("add_term.html", types=types, user=user)


@app.route("/update_term/<term_id>", methods=["GET", "POST"])
def update_term(term_id):
    term = mongo.db.terms.find_one({"_id": ObjectId(term_id)})
    created_by = mongo.db.terms.find_one({"_id": ObjectId(term_id)})['created_by']

    if request.method == "POST":
        
        alt = request.form.get("alt_terms")
        inc = request.form.get("incorrect_terms")

        class Term:

            def __init__(self, to_split):
                self.to_split = to_split

            def split_terms(self):
                request.form.get(self.to_split)
                split_len = len(self.to_split)
                if split_len > 0:
                    return self.to_split.split(",")
                else:
                    return []

        alt_split = Term(alt)
        alternatives = alt_split.split_terms()
        inc_split = Term(inc)
        incorrect = inc_split.split_terms()

        to_update = {
            "term_name": request.form.get("term_name"),
            "alt_terms": alternatives,
            "incorrect_terms": incorrect,
            "usage_notes": request.form.get("usage_notes"),
            "type_name": request.form.get("type_name"),
            "pending": False,
            "last_updated_by": session['user'],
            "created_by": created_by
            }

        mongo.db.terms.update({"_id": ObjectId(term_id)}, to_update)
        flash("Term updated")
        print(created_by)
    
    return redirect(url_for("view_term", term_id=term_id))

    


@app.route("/search_terms", methods=["POST", "GET"])
def search_terms():
    
    query = request.form.get("query")
    terms = list(mongo.db.terms.find({"$text": {"$search": query}}))

    if len(terms) == 0:
        print("no results!")

    user = session['user']

    try:
        pinned_terms = list(mongo.db.users.find_one({"username": user})['pinned_terms'])
    except KeyError:
        pinned_terms = []
    else:
        pinned_terms = list(mongo.db.users.find_one({"username": user})['pinned_terms'])

    return render_template("get_terms.html", terms=terms, user=session['user'], pinned_terms=pinned_terms)


@app.route("/got_to_term/<pinned>")
def go_to_term(pinned):
    pin = mongo.db.terms.find_one({"term_name": pinned})
    term_id = pin["_id"]
    return redirect(url_for("manage_term", term_id=term_id))
   


@app.route("/delete_term/<term_id>")
def delete_term(term_id):
    mongo.db.terms.remove({"_id": ObjectId(term_id)})

    flash("Term successfully deleted")
    return redirect(url_for("get_terms", term_id=term_id))


@app.route("/manage_users", methods=["POST", "GET"])
def manage_users():
    levels = list(mongo.db.access_levels.find().sort("level_name", 1))
    users = list(mongo.db.users.find().sort([("access_level", 1), ("username", 1)]))

    return render_template("manage_users.html", users=users, levels=levels)


@app.route("/search_users", methods=["POST", "GET"])
def search_users():
    query = request.form.get("query")
    levels = list(mongo.db.access_levels.find().sort("level_name", 1))
    users = list(mongo.db.users.find({"$text": {"$search": query}}))
    return render_template("manage_users.html", users=users, levels=levels)


@app.route("/add_user", methods=["GET", "POST"])
def add_user():
    if request.method == "POST":

        new_user = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password")),
            "access_level": request.form.get("access_level_add")
        }

        mongo.db.users.insert_one(new_user)
        flash("New user added")
        return redirect(url_for("manage_users"))


@app.route("/update_user/<user_id>", methods=["POST", "GET"])
def update_user(user_id):
    if request.method == "POST":
        user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
        acc_level = request.form["access_level"]
        
        mongo.db.users.update_one({"_id": user["_id"]}, {"$set": {"access_level": acc_level}})
        
        flash("User's access level updated")
        return redirect(url_for("manage_users", user=user))
    
    flash("User's access level was not updated")
    return redirect(url_for("manage_users", user=user))
    

@app.route("/delete_user/<user_id>")
def delete_user(user_id):
    mongo.db.users.remove({"_id": ObjectId(user_id)})

    flash("User deleted")
    return redirect(url_for("manage_users",  user_id=user_id))


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)



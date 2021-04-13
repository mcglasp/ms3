import os
import random
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


def get_access_level(user):
    user = session['user']
    access_level = mongo.db.users.find_one({"username": user})['access_level'].lower()

    return access_level

                
            


@app.route("/")
@app.route("/dashboard")
def dashboard():  
    
    try:
        user = session['user']
        access_level = get_access_level(user)
        levels = list(mongo.db.access_levels.find())
        terms = list(mongo.db.terms.find())
        random_terms = list(random.choice(terms))
        letters = ['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z']
        incorrect_terms = list(mongo.db.terms.incorrect_terms.find())
        alt_terms = list(mongo.db.terms.alt_terms.find())
        new_registrations = list(mongo.db.users.find({'access_level': 'requested'}))
        flagged_comments = list(mongo.db.comments.find({"flagged": True}))
        suggested_terms = mongo.db.terms.find({"pending": True})
        numbers = ['0','1','2','3','4','5','6','7','8','9']
        general = ['General Usage']


        
        try: 
            pinned_term_ids = list(mongo.db.users.find_one({"username": user})['pinned_terms'])
            pinned_terms = list(mongo.db.terms.find({"_id": {"$in": pinned_term_ids}}))

        except Exception:
            pass
               
        return render_template("dashboard.html", terms=terms, incorrect_terms=incorrect_terms, alt_terms=alt_terms, user=user, access_level=access_level, new_registrations=new_registrations, flagged_comments=flagged_comments, levels=levels, suggested_terms=suggested_terms, pinned_terms=pinned_terms, random_terms=random_terms, letters=letters, numbers=numbers, general=general)
    
    except KeyError:
        return redirect(url_for('login'))


@app.route("/get_category/<letter>")
def get_category(letter):
    terms = list(mongo.db.terms.find({'term_name': {"$regex": '^' + letter, "$options": 'i'}}))

    return render_template('dashboard.html', terms=terms)


@app.route("/delete_flag/<comment_id>")
def delete_flag(comment_id):
    flagged_comment = mongo.db.comments.find_one({"_id": ObjectId(comment_id)})
    update = {"$set": {"flagged": False}}
    mongo.db.comments.update_one(flagged_comment, update)
    print(update)
    
    flash("Flag removed")
    return redirect(url_for("dashboard"))


@app.route("/view_term/<term_id>")
def view_term(term_id):
    user = session['user']
    access_level = get_access_level(user)
    term = mongo.db.terms.find_one({"_id": ObjectId(term_id)})

    try:
        term_creator_user = mongo.db.users.find_one({"_id": term['created_by']})
        term['created_by'] = term_creator_user['username']
    except Exception as e:
       pass

    comments = list(mongo.db.comments.find())
    
    term_comments = mongo.db.comments.find({"rel_term_id": term_id})

    return render_template("view_term.html", term=term, term_comments=term_comments, user=user, comments=comments, access_level=access_level)


@app.route("/manage_term/<term_id>")
def manage_term(term_id):
    user = session['user']
    access_level = get_access_level(user)
    term = mongo.db.terms.find_one({"_id": ObjectId(term_id)})
    incorrect_terms = list(mongo.db.terms.incorrect_terms.find())
    alt_terms = list(mongo.db.terms.alt_terms.find())
    types = list(mongo.db.types.find())
    
    return render_template("manage_term.html", term=term, incorrect_terms=incorrect_terms, alt_terms=alt_terms, types=types, access_level=access_level)


@app.route("/pin_term/<term_id>")
def pin_term(term_id):
    term = mongo.db.terms.find_one({"_id": ObjectId(term_id)})
    users = mongo.db["users"]
    user = session['user']
    pinner = mongo.db.users.find_one({"username": session['user']})
    term_to_pin = {"$push": {"pinned_terms": ObjectId(term_id)}}
    user_record_field = users.count_documents({"$and": [{'_id': pinner['_id']}, {"pinned_terms": term_id}]})

    if user_record_field > 0:
        flash("Sorry, you've already pinned this term")
        return redirect(url_for("dashboard", user=user, term=term))
    else:        
        users.update_one(pinner, term_to_pin)
        flash("Term pinned to your dashboard")

    return redirect(url_for("dashboard", user=user, term=term))


@app.route("/remove_pin/<pinned_term>")
def remove_pin(pinned_term):
    user = session['user']
    mongo.db.users.update_one({"username": user}, {"$pull": {"pinned_terms": ObjectId(pinned_term)}})

    flash("Pin successfully deleted")
    return redirect(url_for("dashboard", user=session['user']))


@app.route("/add_comment/<term_id>", methods=["GET", "POST"])
def add_comment(term_id):
    
    user = session['user']
    user_id = mongo.db.users.find_one({"username": user})['_id']
    

    if request.method == "POST":
        now = datetime.now()
    
        comment = {
            "timestamp": now.strftime("%d/%m/%Y, %H:%M:%S"),
            "comment": request.form.get("comment"),
            "user": user_id,
            "rel_term_id": term_id,
            "flagged": False
            }

        mongo.db.comments.insert_one(comment)
        flash("Hooray it worked!")
        return redirect(url_for("view_term", term_id=term_id))


@app.route("/delete_comment/<comment_id>/<term_id>")
def delete_comment(comment_id, term_id):
    mongo.db.comments.remove({"_id": ObjectId(comment_id)})
    flash("Comment successfully deleted")
    return redirect(url_for("manage_term", term_id=term_id))



@app.route("/flag_comment/<comment_id>/<term_id>")
def flag_comment(comment_id, term_id):
    user = session['user']

    comments = mongo.db["comments"]
    flag_status = comments.find_one({"_id": ObjectId(comment_id)})["flagged"]
    
    if flag_status > True:
        flash("This comment has already been flagged to an administrator")
        return redirect(url_for("view_term", term_id=term_id, user=user))
    else:
        # push id to comment's 'flagged_by' array
        comments.update_one({"_id": ObjectId(comment_id)}, {"$set": {"flagged": True}})
        # push comment_id to user's 'flagged_comments' array
        
        flash("You have flagged this comment")
        return redirect(url_for("view_term", term_id=term_id, user=user))


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
    user = session['user']
    access_level = get_access_level(user)
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

    return render_template("profile.html", access_level=access_level)


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
                    "dashboard", username=session["user"]))

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
    user = session['user']
    access_level = get_access_level(user)

    if session["user"]:
        return render_template("profile.html", user=user, access_level=access_level)

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
    access_level = get_access_level(user)
    database_user = mongo.db.users.find_one({"username": user})

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
            "created_by": ObjectId(database_user['_id'])
            }

        mongo.db.terms.insert_one(term)
        flash("Term added")
        return redirect(url_for("add_term"))

    types = mongo.db.types.find().sort("types", 1)
    return render_template("add_term.html", types=types, user=user, access_level=access_level)


@app.route("/update_term/<term_id>", methods=["GET", "POST"])
def update_term(term_id):
    user = session['user']
    access_level = get_access_level(user)
    term = mongo.db.terms.find_one({"_id": ObjectId(term_id)})
    updated_by = mongo.db.users.find_one({'username': session['user']})

    print(updated_by['username'])
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
            "last_updated_by": ObjectId(updated_by['_id']),
            "created_by": ObjectId(term['created_by'])
            }

        mongo.db.terms.update({"_id": ObjectId(term_id)}, to_update)
        flash("Term updated")
    
    return redirect(url_for("view_term", term_id=term_id, access_level=access_level))

    


@app.route("/search_terms", methods=["POST", "GET"])
def search_terms():
    
    query = request.form.get("query")
    terms = list(mongo.db.terms.find({"$text": {"$search": query}}))

    if len(terms) == 0:
        print("no results!")

    
    return render_template("dashboard.html", terms=terms)


@app.route("/go_to_term/<term_id>")
def go_to_term(term_id):
    user = session['user']
    access_level = get_access_level(user)
    mongo.db.terms.find_one({'_id': ObjectId(term_id)})
    
    return redirect(url_for("view_term", term_id=term_id, access_level=access_level))
   


@app.route("/delete_term/<term_id>")
def delete_term(term_id):
    mongo.db.terms.remove({"_id": ObjectId(term_id)})

    flash("Term successfully deleted")
    return redirect(url_for("dashboard", term_id=term_id))


@app.route("/manage_users", methods=["POST", "GET"])
def manage_users():
    user = session['user']
    access_level = get_access_level(user)
    levels = list(mongo.db.access_levels.find().sort("level_name", 1))
    users = list(mongo.db.users.find().sort([("access_level", 1), ("username", 1)]))

    return render_template("manage_users.html", users=users, levels=levels, access_level=access_level)


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



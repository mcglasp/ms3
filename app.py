import os
import re
from datetime import datetime
from flask import (
    Flask, flash, render_template, 
    redirect, request, session, url_for, g)

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


def page_h3(h3):
    return h3


def get_access_level():
    user = get_record('users', 'username', session['user'])
    user_id = user['_id']
    access_level = mongo.db.users.find_one({"_id": ObjectId(user_id)})['access_level'].lower()

    return access_level


def return_flags():
    records = mongo.db.comments.find({'flagged': True})
    flagged = list(records)
    return flagged


def get_collection(get_col):
    col = mongo.db[get_col]
    collection = col.find()

    return collection
    

def get_record(col, key, val):
    collection = mongo.db[col]
    record = collection.find_one({key: val})
    
    return record


def lets_nums():
    categories = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', '0','1','2','3','4','5','6','7','8','9']

    return categories


def get_pinned_terms():
    user = mongo.db.users.find_one({'username': session['user']})
    
    try: 
        pinned_term_ids = list(user['pinned_terms'])
        pinned_terms = list(mongo.db.terms.find({"_id": {"$in": pinned_term_ids}}))

    except Exception:
        pinned_terms = []

    return pinned_terms


def get_fields(find):

    class Field_name:

        def __init__(self, find):
            self.list = find
        
        def make_list(self):
            name = self.list
            
            items = request.form.getlist(name)
            
            made_list = []
            for item in items:
                if item != "":
                    made_list.append(item)
            
            return made_list

    get_list = Field_name(find)
    return_list = get_list.make_list()

    return return_list


def text_search(user_query):

    def standard_search(input_text):
        terms = list(mongo.db.terms.find({"$text": {"$search": user_query}}))
        
        return terms
    
    terms = standard_search(user_query)
    
    # number change
    if terms == []:
        print('1')
        numbers = {'one': '1', 'two': '2', 'three': '3', 'four': '4', 'five': '5', 'six': '6', 'seven': '7', 'eight': '8', 'nine': '9'}
        for num, dig in numbers.items():
            if num in user_query:
                num_change = re.sub(num, dig, user_query)
                user_query = num_change
                print(2)
                terms = list(mongo.db.terms.find({"$text": {"$search": user_query}}))
                return terms

            elif dig in user_query:
                num_change = re.sub(dig, num, user_query)
                user_query = num_change
                terms = list(mongo.db.terms.find({"$text": {"$search": user_query}}))
                print('3')
                return terms
        
        # strip punctuation
    if terms == []:
        to_remove = "[\s'&/\-.]"
        input_stripped = re.sub(to_remove, '', user_query)
        print('4')
        terms = list(mongo.db.terms.find({"$text": {"$search": input_stripped}}))

        
        print('here, terms is []')
        # regex search
    if terms == []:
        print('5')

        pattern = f"({user_query[0]})[{user_query[1:]}]"+"{3,}"
        print(pattern)
        terms = list(mongo.db.terms.find({'term_name': {"$regex": pattern, "$options": 'gmi'}}))
    
        return terms

    print('6')
    return terms



def get_user():
    user = mongo.db.users.find_one({'username': session['user']})
    username = user['username']
    
    return user, username


@app.context_processor
def inject_notifications():
    new_registrations = list(mongo.db.users.find({'access_level':'requested'}))
    flagged_comments = list(mongo.db.comments.find({'flagged': True}))
    suggested_terms = list(mongo.db.terms.find({'pending': True}))
    g.notifications = len(suggested_terms) + len(flagged_comments) + len(new_registrations)

    return dict(notifications=g.notifications)


@app.route("/")
@app.route("/dashboard")
def dashboard():  
    
    categories = lets_nums()
    
    try:
        user = get_record('users', 'username', session['user'])
        h3_var = user['username']
        this_h3 = page_h3(f"{h3_var}'s Dashboard")
        access_level = get_access_level()
        levels = list(get_collection('access_levels').sort("level_name", 1))
        terms = None
        new_registrations = list(mongo.db.users.find({'access_level':'requested'}))
        flagged_comments = list(mongo.db.comments.find({'flagged': True}))
        suggested_terms = list(mongo.db.terms.find({'pending': True}))
        notifications = len(suggested_terms) + len(flagged_comments) + len(new_registrations)

        pinned_terms = get_pinned_terms()

        def manage_flagged_comments(flagged):
            term_id = flagged['rel_term_id']
            term_name = get_record('terms', '_id', ObjectId(term_id))
            return term_name['term_name']
        
        def manage_suggested_terms(suggestion):
            suggestion_user = suggestion['created_by']
            try:
                suggested_by = mongo.db.users.find_one({'_id': ObjectId(suggestion_user)})['username']
                
            except Exception:
                suggested_by = ""
            
            return suggested_by

    except KeyError:
        return redirect(url_for('login'))
            
    return render_template("dashboard.html", notifications=notifications, this_h3=this_h3, terms=terms, user=user, access_level=access_level, new_registrations=new_registrations, flagged_comments=flagged_comments, levels=levels, suggested_terms=suggested_terms, pinned_terms=pinned_terms, categories=categories, manage_flagged_comments=manage_flagged_comments, manage_suggested_terms=manage_suggested_terms)
     

@app.route("/get_category/<category>")
def get_category(category):
    user = get_record('users', 'username', session['user'])
    h3_var = user['username']
    this_h3 = page_h3(f"{h3_var}'s Dashboard")
    new_registrations = list(mongo.db.users.find({'access_level':'requested'}))
    flagged_comments = list(mongo.db.comments.find({'flagged': True}))
    suggested_terms = list(mongo.db.terms.find({'pending': True}))
    notifications = len(suggested_terms) + len(flagged_comments) + len(new_registrations)
    categories = lets_nums()
    access_level = get_access_level()
    pinned_terms = get_pinned_terms()
    terms = list(mongo.db.terms.find({'term_name': {"$regex": '^' + category, "$options": 'i'}}))

    def manage_flagged_comments(flagged):
        term_id = flagged['rel_term_id']
        term_name = get_record('terms', '_id', ObjectId(term_id))
        return term_name['term_name']
    
    def manage_suggested_terms(suggestion):
        suggestion_user = suggestion['created_by']
        try:
            suggested_by = mongo.db.users.find_one({'_id': ObjectId(suggestion_user)})['username']

        except Exception:
            suggested_by = ""
        
        return suggested_by


    return render_template('dashboard.html', notifications=notifications, this_h3=this_h3, manage_flagged_comments=manage_flagged_comments, suggested_terms=suggested_terms, flagged_comments=flagged_comments, new_registrations=new_registrations, terms=terms, access_level=access_level, user=user, categories=categories, pinned_terms=pinned_terms)


@app.route("/delete_flag/<comment_id>")
def delete_flag(comment_id):
    flagged_comment = get_record('comments', '_id', ObjectId(comment_id))
    update = {"$set": {"flagged": False}}
    mongo.db.comments.update_one(flagged_comment, update)

    flash("Flag removed")
    return redirect(url_for("dashboard"))


@app.route("/view_term/<term_id>")
def view_term(term_id):
    user = get_record('users', 'username', session['user'])
    access_level = get_access_level()
    term = get_record('terms', '_id', ObjectId(term_id))
    
    term_comments = list(mongo.db.comments.find({'rel_term_id': term_id}))
    
    def find_commenter(term_comment):
        
        try:
            term_comment_user = mongo.db.users.find_one({'_id': ObjectId(term_comment['user'])})
            commenter = term_comment_user['username']
        except TypeError:
            commenter = ""
        
        return commenter

    try:
        term_creator_user = get_record('users', '_id', term['created_by'])
        term['created_by'] = term_creator_user['username']

    except Exception:
        term['created_by'] = "Username not given"
        
    try:
        term_updated_by = get_record('users', '_id', term['last_updated_by'])
        term['last_updated_by'] = term_updated_by['username']
        
    except Exception:
        term['last_updated_by'] = ""

    return render_template("view_term.html", term=term, term_comments=term_comments, user=user, access_level=access_level, find_commenter=find_commenter)


@app.route("/manage_term/<term_id>")
def manage_term(term_id):
    user = get_record('users', 'username', session['user'])
    access_level = get_access_level()
    term = get_record('terms', '_id', ObjectId(term_id))
    types = get_collection('types')
    
    return render_template("manage_term.html", term=term, types=types, access_level=access_level, user=user)


@app.route("/pin_term/<term_id>")
def pin_term(term_id):
    origin = request.args['origin']
    term = get_record('terms', '_id', ObjectId(term_id))
    user = get_record('users', 'username', session['user'])
    term_to_pin = {"$push": {"pinned_terms": ObjectId(term_id)}}
    user_query = {'_id': ObjectId(user['_id'])}
    user_record_field = mongo.db.users.count_documents({"$and":  [user_query, {"pinned_terms": ObjectId(term_id)}]})

    if user_record_field > 0:
        flash("Sorry, you've already pinned this term")
        if origin == 'dash':
            return redirect(url_for("dashboard", user=user, term=term))
        else:
            return redirect(url_for("view_term", term_id=term_id))
    else:        
        mongo.db.users.update_one(user, term_to_pin)
        flash("Term pinned to your dashboard")

    if origin == 'dash':
        return redirect(url_for("dashboard", user=user, term=term))
    else:
        return redirect(url_for("view_term", term_id=term_id))


@app.route("/remove_pin/<pinned_term>")
def remove_pin(pinned_term):
    user = get_record('users', 'username', session['user'])
    mongo.db.users.update_one({"username": user['username']}, {"$pull": {"pinned_terms": ObjectId(pinned_term)}})
    flash("Pin successfully deleted")
    return redirect(url_for("dashboard", user=user))


@app.route("/add_comment/<term_id>", methods=["GET", "POST"])
def add_comment(term_id):
    user = get_record('users', 'username', session['user'])
    user_id = user['_id']

    comment_field = request.form.get("comment")
    if comment_field != "":

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
    
    else:
        flash("Please add a comment")

    return redirect(url_for("view_term", term_id=term_id))


@app.route("/delete_comment/<comment_id>/<term_id>")
def delete_comment(comment_id, term_id):
    mongo.db.comments.remove({"_id": ObjectId(comment_id)})
    flash("Comment successfully deleted")
    return redirect(url_for("view_term", term_id=term_id))


@app.route("/flag_comment/<comment_id>/<term_id>")
def flag_comment(comment_id, term_id):
    user = get_record('users', 'username', session['user'])
    flag_attempt = get_record('comments', '_id', ObjectId(comment_id))
    flag_status = flag_attempt['flagged']

    if flag_status:
        flash("This comment has already been flagged to an administrator")
        return redirect(url_for("view_term", term_id=term_id, user=user))
    else:
        flag_update = {"$set": {"flagged": True}}
        mongo.db.comments.update_one(flag_attempt, flag_update)

        flash("You have flagged this comment")
        return redirect(url_for("view_term", term_id=term_id, user=user, comment_id=comment_id))
    

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
            "access_level": "requested",
            "to_change_pword": False
        }
        mongo.db.users.insert_one(register)
        
        # Put the new user into 'session' cookie
        session["user"] = request.form.get("username").lower()
        flash("Your registration request has been sent to the administrator")
        return redirect(url_for("register"))

    return render_template("register.html")


@app.route("/change_password/<user_id>", methods=["GET", "POST"])
def change_password(user_id):
    user = get_record('users', 'username', session['user'])
    access_level = get_access_level()
    users = mongo.db["users"]
    existing_user = users.find_one(
        {"username": request.form.get("username").lower()}) 
    to_change_pword = existing_user['to_change_pword']

    if request.method == "POST":
        new_password = request.form.get("new_password")

        if existing_user:
            if check_password_hash(existing_user["password"], request.form.get("password")):
                to_update = {"_id": existing_user["_id"]}
                if to_change_pword == True:
                    updated_password = {"$set": {"password": generate_password_hash(new_password), 'to_change_pword': False}}
                    
                else:
                    updated_password = {"$set": {"password": generate_password_hash(new_password)}}
                users.update_one(to_update, updated_password)
                flash("Password successfully updated")
                return redirect(url_for(
                "profile", user=user, access_level=access_level))

            else:
                # invalid password match
                flash("Incorrect Username and/or Current Password")
                return redirect(url_for("profile", user=user, access_level=access_level))

        else:
            # username doesn't exist
            flash("Incorrect Username and/or Current Password")
            return redirect(url_for('profile', user=user, access_level=access_level))

    return render_template("profile.html", user=user, access_level=access_level)


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
                return redirect(url_for(
                    "dashboard", user=session['user']))

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
    user = get_record('users', 'username', session['user'])
    access_level = get_access_level()
    to_change_pword = user['to_change_pword']

    if session["user"]:
        return render_template("profile.html", user=user, access_level=access_level, to_change_pword=to_change_pword)

    return redirect(url_for("login"))


@app.route("/logout")
def logout():
    # remove user from session cookies
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("login"))


@app.route("/add_term", methods=["GET", "POST"])
def add_term():  
    user = get_record('users', 'username', session['user'])
    access_level = get_access_level()

    if request.method == "POST":
        alternatives = get_fields("alt_terms")
        incorrect = get_fields("incorrect_terms")
        term_name = request.form.get("term_name")

        term = {
            "term_name": term_name,
            "alt_terms": alternatives,
            "incorrect_terms": incorrect,
            "usage_notes": request.form.get("usage_notes"),
            "type_name": request.form.get("type_name"),
            "pending": False if access_level == 'administrator' else True,
            "created_by": ObjectId(user['_id'])
            }

        mongo.db.terms.insert_one(term)
        flash("Term added")
        return redirect(url_for("add_term"))

    types = mongo.db.types.find().sort("types", 1)
    return render_template("add_term.html", types=types, user=user, access_level=access_level)



@app.route("/update_term/<term_id>", methods=["GET", "POST"])
def update_term(term_id):
    user = get_record('users', 'username', session['user'])
    access_level = get_access_level()
    term = get_record('terms', '_id', ObjectId(term_id))

    if request.method == "POST":

        incorrect = get_fields("incorrect_terms")
        alternatives = get_fields("alt_terms")
        try:
            created_by = term['created_by']
        except KeyError:
            created_by = 'Creator not recorded'

        update_term = {
            "term_name": request.form.get("term_name"),
            "alt_terms": alternatives,
            "incorrect_terms": incorrect,
            "usage_notes": request.form.get("usage_notes"),
            "type_name": request.form.get("type_name"),
            "pending": False if access_level == 'administrator' else True,
            "created_by": created_by,
            "last_updated_by": ObjectId(user['_id'])
            }
        
        mongo.db.terms.update({"_id": ObjectId(term_id)}, update_term)

    flash("Term successfully updated")
    return redirect(url_for("dashboard"))


@app.route("/search_terms", methods=["POST", "GET"])
def search_terms():
    user = get_record('users', 'username', session['user'])
    h3_var = user['username']
    this_h3 = page_h3(f"{h3_var}'s Dashboard")
    new_registrations = list(mongo.db.users.find({'access_level':'requested'}))
    flagged_comments = list(mongo.db.comments.find({'flagged': True}))
    suggested_terms = list(mongo.db.terms.find({'pending': True}))
    
    access_level = get_access_level()
    categories = lets_nums()
    query = request.form.get('query')
    pinned_terms = get_pinned_terms()
    
    try:
        terms = text_search(query)
    
    except IndexError:
        terms = None
    
    def manage_flagged_comments(flagged):
        term_id = flagged['rel_term_id']
        term_name = get_record('terms', '_id', ObjectId(term_id))
        return term_name['term_name']
    
    def manage_suggested_terms(suggestion):
        suggestion_user = suggestion['created_by']
        try:
            suggested_by = mongo.db.users.find_one({'_id': ObjectId(suggestion_user)})['username']

        except Exception:
            suggested_by = ""
        
        return suggested_by

    return render_template("dashboard.html", this_h3=this_h3, flagged_comments=flagged_comments, suggested_terms=suggested_terms, manage_flagged_comments=manage_flagged_comments, manage_suggested_terms=manage_suggested_terms, new_registrations=new_registrations, user=user, terms=terms, categories=categories, access_level=access_level, pinned_terms=pinned_terms)


@app.route("/go_to_term/<term_id>")
def go_to_term(term_id):
    access_level = get_access_level()
    mongo.db.terms.find_one({'_id': ObjectId(term_id)})
    
    return redirect(url_for("view_term", term_id=term_id, access_level=access_level))
   


@app.route("/delete_term/<term_id>")
def delete_term(term_id):
    mongo.db.terms.remove({"_id": ObjectId(term_id)})

    flash("Term successfully deleted")
    return redirect(url_for("dashboard", term_id=term_id))


@app.route("/manage_users", methods=["POST", "GET"])
def manage_users():
    this_h3 = page_h3("Manage users")
    access_level = get_access_level()
    levels = list(mongo.db.access_levels.find().sort("level_name", 1))
    users_list = list(mongo.db.users.find().sort([("access_level", 1), ("username", 1)]))

    return render_template("manage_users.html", users_list=users_list, levels=levels, access_level=access_level, this_h3=this_h3)


@app.route("/search_users", methods=["POST", "GET"])
def search_users():
    query = request.form.get("query")
    levels = list(mongo.db.access_levels.find().sort("level_name", 1))
    users_list = list(mongo.db.users.find({"$text": {"$search": query}}))
    return render_template("manage_users.html", users_list=users_list, levels=levels)


@app.route("/add_user", methods=["GET", "POST"])
def add_user():
    if request.method == "POST":

        new_user = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password")),
            "access_level": request.form.get("access_level_add"),
            "to_change_pword": True
        }

        mongo.db.users.insert_one(new_user)
        flash("New user added")
        return redirect(url_for("manage_users"))


@app.route("/update_user/<each_user_id>", methods=["POST", "GET"])
def update_user(each_user_id):
    origin = request.args['origin']
    
    if request.method == "POST":
        user_to_update = get_record('users', '_id', ObjectId(each_user_id))
        acc_level = request.form["access_level"]
        mongo.db.users.update_one({"_id": user_to_update["_id"]}, {"$set": {"access_level": acc_level}})

        flash("User's access level updated")

        if origin == 'dash':
            return redirect(url_for("dashboard"))
        else:
            return redirect(url_for("manage_users", user_to_update=user_to_update))
        

    flash("User's access level was not updated")
    return redirect(url_for("manage_users", user_to_update=user_to_update))


@app.route("/delete_user/<each_user_id>")
def delete_user(each_user_id):
    mongo.db.users.remove({"_id": ObjectId(each_user_id)})

    flash("User deleted")
    return redirect(url_for("manage_users"))


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)



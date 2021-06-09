import os
import re
from datetime import datetime
from flask import (
    Flask, flash, render_template, 
    redirect, request, session, url_for, g)

from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
import werkzeug.exceptions


if os.path.exists("env.py"):
    import env


app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")




mongo = PyMongo(app)


def check_user_login():
    try:
        if session["user"] is not None:
            return True
    except:
        return False


def page_h3(h3):
    return h3


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

    terms = []
    found = None
    
    def standard_search(user_query):
        found = list(mongo.db.terms.find({"$text": {"$search": user_query}}))
        if found != None:
            terms.extend(found)

        return terms
    
    terms = standard_search(user_query)

    if (terms == []) or (len(terms) < 2) or ((len(terms) == 1) and (terms[0]['pending'] == True)):
        input_stripped = re.sub("[\s'&/\-.]", '', user_query)
        
        found = list(mongo.db.terms.find({"$text": {"$search": input_stripped}}))
        terms.extend(found)




   
    return terms


@app.context_processor


@app.context_processor
def inject_user():
    
    try:
        g.user = mongo.db.users.find_one({'username': session['user']})
        user_id = g.user['_id'] if g.user else None
        g.access_level = mongo.db.users.find_one({"_id": ObjectId(user_id)})['access_level'].lower() if user_id else 'requested'

        try:
            user_for_header = g.user['username'].capitalize()
            g.this_h3 = page_h3(f"{user_for_header}'s Account")
        
        except TypeError:
            user_for_header = ""
            this_h3 = page_h3("Dashboard")
        
        return dict(user=g.user, access_level=g.access_level, this_h3=g.this_h3)

    except KeyError:
        g.user = None

    except AttributeError:
        pass
    
    return dict(user=g.user)


@app.context_processor
def inject_notifications():
    g.new_registrations = list(mongo.db.users.find({'access_level': 'requested'}))
    g.flagged_comments = list(mongo.db.comments.find({'flagged': True}))
    g.suggested_terms = list(mongo.db.terms.find({'pending': True}))
    g.notifications = len(g.suggested_terms) + len(g.flagged_comments) + len(g.new_registrations)
    g.term_updates = list(mongo.db.terms.find().sort("last_updated", -1).limit(5))
    g.recent_comments = list(mongo.db.comments.find().sort("_id", -1).limit(5))
    g.categories = lets_nums()
    

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
    
    def term_comment(comment):
        try:
            rel_term_id = comment['rel_term_id']
            related_term = mongo.db.terms.find_one({'_id': ObjectId(rel_term_id)})
            
            if related_term != "":
                related_term_name = related_term['term_name']
                return related_term_name, rel_term_id
            else:
                return None
        
        except TypeError:
            related_term_name = ""

        except KeyError:
            related_term_name = ""


    return dict(categories=g.categories, term_comment=term_comment, manage_flagged_comments=manage_flagged_comments, manage_suggested_terms=manage_suggested_terms, notifications=g.notifications, new_registrations=g.new_registrations, suggested_terms=g.suggested_terms, flagged_comments=g.flagged_comments, term_updates=g.term_updates, recent_comments=g.recent_comments)


@app.context_processor
def get_pinned_terms():
    user = inject_user()

    try:
        pinned_terms = user['user']['pinned_terms']
        pinned_term_ids = list(pinned_terms)
        g.pinned_terms = list(mongo.db.terms.find({"_id": {"$in": pinned_term_ids}}))

    except Exception:
        g.pinned_terms = []

    return dict(pinned_terms=g.pinned_terms)


@app.route("/")
@app.route("/dashboard")
def dashboard():
    if check_user_login() is True:
        try:
            get_user = inject_user()

        except AttributeError:
            
            return redirect(url_for("login"))
    
        if get_user['user'] is None:
            return redirect(url_for("login"))
        

        categories = lets_nums()
        levels = list(get_collection('access_levels').sort("level_name", 1))
        terms = None
        
        return render_template("dashboard.html", terms=terms, levels=levels, categories=categories)
    
    return redirect(url_for("login"))


@app.route("/get_category/<category>")
def get_category(category):
    if check_user_login() is True:
        categories = lets_nums()
        terms = list(mongo.db.terms.find({'term_name': {"$regex": '^' + category, "$options": 'i'}}))

        return render_template('dashboard.html', terms=terms, categories=categories)

    return redirect(url_for("login"))

@app.route("/delete_flag/<comment_id>")
def delete_flag(comment_id):
    if check_user_login() is True:
        flagged_comment = get_record('comments', '_id', ObjectId(comment_id))
        update = {"$set": {"flagged": False}}
        mongo.db.comments.update_one(flagged_comment, update)

        flash("Flag removed")
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/view_term/<term_id>")
def view_term(term_id):
    if check_user_login() is True:
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
            created_by = term['created_by']

        except TypeError:
            created_by = ""
    
        try:
            term_updated_by = get_record('users', '_id', term['last_updated_by'])
            term['last_updated_by'] = term_updated_by['username']
            last_updated_by = term['last_updated_by']

        except Exception:
            last_updated_by = ""

        return render_template("view_term.html", term=term, term_comments=term_comments, find_commenter=find_commenter, created_by=created_by, last_updated_by=last_updated_by)
    return redirect(url_for("login"))

@app.route("/manage_term/<term_id>")
def manage_term(term_id):
    if check_user_login() is True:
        term = get_record('terms', '_id', ObjectId(term_id))
        types = get_collection('types')
    
        return render_template("manage_term.html", term=term, types=types)
    return redirect(url_for("login"))

@app.route("/pin_term/<term_id>")
def pin_term(term_id):
    if check_user_login() is True:
        origin = request.args['origin']
        term = get_record('terms', '_id', ObjectId(term_id))
        user_record = inject_user()
        user = user_record['user']
        user_id = user_record['user']['_id']
        term_to_pin = {"$push": {"pinned_terms": ObjectId(term_id)}}
        user_query = {'_id': ObjectId(user_id)}
        user_record_field = mongo.db.users.count_documents({"$and":  [user_query, {"pinned_terms": ObjectId(term_id)}]})

        if user_record_field > 0:
            flash("Sorry, you've already pinned this term")
            if origin == 'dash':
                return redirect(url_for("dashboard", term_id=term_id))
            else:
                return redirect(url_for("view_term", term_id=term_id))

        else:
            mongo.db.users.update_one(user, term_to_pin)
            flash("Term pinned to your dashboard")

        if origin == 'dash':
            return redirect(url_for("dashboard", term_id=term_id))
        else:
            return redirect(url_for("view_term", term_id=term_id))
    return redirect(url_for("login"))

@app.route("/remove_pin/<pinned_term>")
def remove_pin(pinned_term):
    if check_user_login() is True:
        user_record = inject_user()
        username = user_record['user']['username']

        mongo.db.users.update_one({"username": username}, {"$pull": {"pinned_terms": ObjectId(pinned_term)}})
        flash("Pin successfully deleted")
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/add_comment/<term_id>", methods=["GET", "POST"])
def add_comment(term_id):
    if check_user_login() is True:
        user_record = inject_user()
        user_id = user_record['user']['_id']

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
                flash("Comment added")

        else:
            flash("Please add a comment")

        return redirect(url_for("view_term", term_id=term_id))
    return redirect(url_for("login"))

@app.route("/delete_comment/<comment_id>/<term_id>")
def delete_comment(comment_id, term_id):
    if check_user_login() is True:
        mongo.db.comments.remove({"_id": ObjectId(comment_id)})
        flash("Comment successfully deleted")
        return redirect(url_for("view_term", term_id=term_id))
    return redirect(url_for("login"))

@app.route("/flag_comment/<comment_id>/<term_id>")
def flag_comment(comment_id, term_id):
    if check_user_login() is True:
        flag_attempt = get_record('comments', '_id', ObjectId(comment_id))
        flag_status = flag_attempt['flagged']

        if flag_status:
            flash("This comment has already been flagged to an administrator")
            return redirect(url_for("view_term", term_id=term_id))
        else:
            flag_update = {"$set": {"flagged": True}}
            mongo.db.comments.update_one(flag_attempt, flag_update)

            flash("You have flagged this comment")
            return redirect(url_for("view_term", term_id=term_id, comment_id=comment_id))
    return redirect(url_for("login"))

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

        flash("Your registration request has been sent to the administrator")
        return redirect(url_for("register"))

    return render_template("register.html")


@app.route("/change_password/<user_id>", methods=["GET", "POST"])
def change_password(user_id):
    if check_user_login() is True:
        user_record = inject_user()
        user = user_record['user']
        users = mongo.db["users"]
        to_change_pword = user['to_change_pword']

        if request.method == "POST":
            new_password = request.form.get("new_password")
            get_repeat = request.form.get("repeat_new_password")

            if user:
                if check_password_hash(user["password"], request.form.get("password")):
                    to_update = {"_id": user["_id"]}
                    if new_password == get_repeat:

                        if to_change_pword == True:
                            updated_password = {"$set": {"password": generate_password_hash(new_password), 'to_change_pword': False}}
        
                        else:
                            updated_password = {"$set": {"password": generate_password_hash(new_password)}}
                    
                    else:
                        flash("New password and repeat password must match")
                        return redirect(url_for("profile", user=user))                   

                    users.update_one(to_update, updated_password)
                    flash("Password successfully updated")
                    return redirect(url_for("profile", user=user))

                else:
                    # invalid password match
                    flash("Incorrect current password")
                    return redirect(url_for("profile", user=user))

            else:
                # username doesn't exist
                flash("Incorrect Username and/or Current Password")
                return redirect(url_for('profile', user=user))

        return render_template("profile.html", user=user)
    return redirect(url_for("login"))

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
    if check_user_login() is True:
        user_record = inject_user()
        user = user_record['user']
        to_change_pword = user['to_change_pword']

        return render_template("profile.html", to_change_pword=to_change_pword)

    return redirect(url_for('login'))

@app.route("/logout")
def logout():
    # remove user from session cookies
    session.pop("user")
    return redirect(url_for("login"))


@app.route("/add_term", methods=["GET", "POST"])
def add_term():
    if check_user_login() is True:
        user_record = inject_user()
        user_id = user_record['user']['_id']
        access_level = user_record['access_level']

        if request.method == "POST":
            now = datetime.now()
            alternatives = get_fields("alt_terms")
            incorrect = get_fields("incorrect_terms")
            term_name = request.form.get("term_name")
            type_name = request.form.get("type_name")
            type_suggest = 'What type of term is this? Suggest something.'


            term = {
                "term_name": term_name,
                "alt_terms": alternatives,
                "incorrect_terms": incorrect,
                "usage_notes": request.form.get("usage_notes"),
                "type_name": type_name if type_name != None else type_suggest,
                "pending": False if access_level == 'administrator' else True,
                "created_by": ObjectId(user_id),
                "last_updated": now.strftime("%d/%m/%Y")
                }

            mongo.db.terms.insert_one(term)
            if access_level == 'administrator':
                flash("Term added")
            else:
                flash("Your suggestion has been sent to the Administrator")
            return redirect(url_for("add_term"))

        types = mongo.db.types.find().sort("types", 1)
        return render_template("add_term.html", types=types)
    return redirect(url_for("login"))

@app.route("/update_term/<term_id>", methods=["GET", "POST"])
def update_term(term_id):
    if check_user_login() is True:
        user_record = inject_user()
        user_id = user_record['user']['_id']
        access_level = user_record['user']['access_level']
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
                "last_updated_by": ObjectId(user_id)
                }

            mongo.db.terms.update({"_id": ObjectId(term_id)}, update_term)

        flash("Term successfully updated")
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/search_terms", methods=["POST", "GET"])
def search_terms():
    if check_user_login() is True:
        categories = lets_nums()
        query = request.form.get('query')

        try:
            terms = text_search(query)
            print(type(terms))

        except IndexError:
            terms = None

        return render_template("dashboard.html", terms=terms, categories=categories)
    return redirect(url_for("login"))

@app.route("/go_to_term/<term_id>")
def go_to_term(term_id):
    if check_user_login() is True:
        mongo.db.terms.find_one({'_id': ObjectId(term_id)})

        return redirect(url_for("view_term", term_id=term_id))
    return redirect(url_for("login"))

@app.route("/delete_term/<term_id>")
def delete_term(term_id):
    if check_user_login() is True:
        # find pins related to term
        find_pins_users = list(mongo.db.users.find({"pinned_terms": {"$in": [ObjectId(term_id)]}}))
        # delete pin references from user accounts
        for pin_user in find_pins_users:
            mongo.db.users.update_one(pin_user, {"$pull": {"pinned_terms": ObjectId(term_id)}})
        # find and delete comments relating to term
        mongo.db.comments.remove({"rel_term_id": term_id})

        mongo.db.terms.remove({"_id": ObjectId(term_id)})


        flash("Term successfully deleted")
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/manage_users")
def manage_users():
    if check_user_login() is True:
        users_list = None
        levels = list(mongo.db.access_levels.find().sort("level_name", 1))

        return render_template("manage_users.html", users_list=users_list, levels=levels)
    return redirect(url_for("login"))

@app.route("/show_all_users")
def show_all_users():
    if check_user_login() is True:
        levels = list(mongo.db.access_levels.find().sort("level_name", 1))
        users_list = list(mongo.db.users.find().sort([("access_level", 1), ("username", 1)]))

        return render_template("manage_users.html", users_list=users_list, levels=levels)
    return redirect(url_for("login"))

@app.route("/search_users", methods=["POST", "GET"])
def search_users():
    if check_user_login() is True:
        query_user = request.form.get("query_user")
        levels = list(mongo.db.access_levels.find().sort("level_name", 1))
        users_list = list(mongo.db.users.find({"$text": {"$search": query_user}}))
        return render_template("manage_users.html", users_list=users_list, levels=levels)
    return redirect(url_for("login"))

@app.route("/add_user", methods=["GET", "POST"])
def add_user():
    if check_user_login() is True:
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
    return redirect(url_for("login"))

@app.route("/update_user/<each_user_id>", methods=["POST", "GET"])
def update_user(each_user_id):
    if check_user_login() is True:
        origin = request.args['origin']

        if request.method == "POST":
            user_to_update = get_record('users', '_id', ObjectId(each_user_id))
            acc_level = request.form.get("access_level")
            mongo.db.users.update_one({"_id": user_to_update["_id"]}, {"$set": {"access_level": acc_level}})

            flash("User's access level updated")

            if origin == 'dash':
                return redirect(url_for("dashboard"))
            else:
                return redirect(url_for("manage_users", user_to_update=user_to_update))

        flash("Sorry, looks like there's been an error updating this user")
        return redirect(url_for("manage_users"))
    return redirect(url_for("login"))

@app.route("/manage_user_sidenav/<each_user_id>")
def manage_user_sidenav(each_user_id):
    if check_user_login() is True:
        user_to_find = mongo.db.users.find_one({'_id': ObjectId(each_user_id)})
        query_user = user_to_find['username']
        users_list = list(mongo.db.users.find({"$text": {"$search": query_user}}))
        levels = list(mongo.db.access_levels.find().sort("level_name", 1))
        return render_template("manage_users.html", users_list=users_list, levels=levels)
    return redirect(url_for("login"))

@app.route("/delete_user/<each_user_id>")
def delete_user(each_user_id):
    if check_user_login() is True:
        mongo.db.users.remove({"_id": ObjectId(each_user_id)})

        flash("User deleted")
        return redirect(url_for("manage_users"))
    return redirect(url_for("login"))

@app.errorhandler(404)
def page_not_found(e):
    session_user = inject_user()
    print(session_user)
    return render_template('404.html', session_user=session_user), 404


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)



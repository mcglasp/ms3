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



def recs_cols(which):
    db = mongo.db
    col = db[which]
    if which == 'terms':
        terms = col.find()
        return terms
    elif which == 'users':
        users = col.find()
        return users
    else:
        return None

call = recs_cols('users')
ret_call = list(call)
print(ret_call)
        





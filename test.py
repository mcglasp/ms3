import os
from selenium import webdriver
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


def get_collections(**what):
    col_var = what["col"]
    collection = mongo.db[col_var]
    find_col = collection.find()
    if what['list_it'] == True:
        collect_return = list(find_col)
        print(collect_return)
        return collect_return
    else:
        collect_return = find_col
        print(collect_return)
        return collect_return
    
    


get_collections(col = "terms", list_it = False)
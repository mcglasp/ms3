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




class Cols_and_records:

    def __init__(self, **details):
        self.val = details['val'] 
        self.key = details['key'] 
        self.col = details['col']
 
    def find_col(self, col):
        self.get_col = mongo.db[col]
        self.col_found = self.get_col.find()
        return self.get_col, self.col_found
    
    def find_rec(self, get_col, key, val):
        key = str(key)
        if key == '_id':
            record = get_col.find_one({key: ObjectId(val)})
        else:
            record = get_col.find_one({key: val})

        return record
    

def get_access():

    cr = Cols_and_records(col='users', key='access_level', val='requested')
    cr.find_col(cr.col)
    a = cr.find_rec(cr.get_col, cr.key, cr.val)
    print(a['username'])


get_access()






import os
import re

import os.path
if not os.path.exists("indexdir"):
    os.mkdir("indexdir")
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

   terms = standard_search(user_query)
    
        # strip punctuation
    if (terms == []) or (len(terms) < 2) or ((len(terms) == 1) and (terms[0]['pending'] == True)):
        input_stripped = re.sub("[\s'&/\-.]", '', user_query)
        print(5)
        terms = list(mongo.db.terms.find({"$text": {"$search": input_stripped}}))

        # regex search
    if (terms == []) or (len(terms) < 1) or ((len(terms) == 1) and (terms[0]['pending'] == True)):
        print(6)

        pattern = f"({input_stripped[0]})[{input_stripped[1:]}]"+"{2,}"
        terms = list(mongo.db.terms.find({'term_name': {"$regex": pattern, "$options": 'gmi'}}))
    
        # number change
    if (terms == []) or (len(terms) < 2) or ((len(terms) == 1) and (terms[0]['pending'] == True)):
        numbers = {'one': '1', 'two': '2', 'three': '3', 'four': '4', 'five': '5', 'six': '6', 'seven': '7', 'eight': '8', 'nine': '9'}
        
        for num, dig in numbers.items():
            if num in user_query:
                num_change = re.sub(num, dig, user_query)
                user_query = num_change
                terms = list(mongo.db.terms.find({"$text": {"$search": user_query}}))
                print('numbers', user_query)
                return terms

            elif dig in user_query:
                num_change = re.sub(dig, num, user_query)
                user_query = num_change
                terms = list(mongo.db.terms.find({"$text": {"$search": user_query}}))
                print('numbers', user_query)
                return terms
        print(7)
        return terms
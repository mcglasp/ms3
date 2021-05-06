
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
        terms = list(mongo.db.terms.find({"$text": {"$search": user_query}}))

        
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
    

a = text_search('plginu')
print(a)




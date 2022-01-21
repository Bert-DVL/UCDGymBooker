from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

#The app is a Flask object, __name__ is the name of the current Python module
app = Flask(__name__)

#The database URI that should be used for the connection
#three slashes is relative path, four is absolute path, two slashes if for when you have an authority component
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

#Each Flask web application contains a secret key which used to sign session cookies for protection against cookie data tampering
app.config['SECRET_KEY'] = "ODBHfVNyiVkoFU79KVOIY9GWS7DPzpWE"

#initialise the database with the settings of our app
db = SQLAlchemy(app)

#encryption tool for password hashing
bcrypt = Bcrypt(app)


from ucdgymbooker import routes






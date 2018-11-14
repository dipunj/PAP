from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# project_dir   = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(app.root_path, 'db/')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


database_file = "sqlite:///{}".format(os.path.join(UPLOAD_FOLDER, "users.db"))
app.config["SQLALCHEMY_DATABASE_URI"] = database_file


db = SQLAlchemy(app)



class User(db.Model):
    # __tablename__ = 'users'

    username = db.Column(db.String(8),unique=True, primary_key=True, nullable=False)
    password = db.Column(db.String(80))
    name = db.Column(db.String,nullable=False)
    group_position = db.Column(db.Integer, default=0)

    def __init__(self, username, password, name):
        self.username = username
        self.password = password
        self.name = name

        def __repr__(self):
         return "<Reg. {}><Username: {}><Group : Position {}>".format(self.username,self.username,self.group_position)

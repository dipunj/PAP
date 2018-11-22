from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

#          project_dir      = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER    = os.path.join(app.root_path, 'db/')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


database_file    = "sqlite:///{}".format(os.path.join(UPLOAD_FOLDER, "users.db"))
app.config["SQLALCHEMY_DATABASE_URI"] = database_file


db = SQLAlchemy(app)



class User(db.Model): 
    # __tablename__ = 'users'

    username      = db.Column(db.String(8),unique=True, primary_key=True, nullable=False)
    password      = db.Column(db.String(80))
    name          = db.Column(db.String,nullable=False)
    cpi           = db.Column(db.Float,nullable=False)

    # seperator is $#
    member_string = db.Column(db.String)

    # seperator is $#
    pref_order    = db.Column(db.String)

    def __init__(self, username, password, name, cpi, group_size): 
        self.username          = username
        self.password          = password
        self.name              = name
        self.cpi               = cpi
        self.all_member_string = "1,"+username+","+name+","+str(cpi)+"$#"
        pass

    def addMember(self, group_position, mem_name,mem_cpi,mem_reg_no): 
        self.member_string += str(group_position)+","+str(mem_reg_no)+","+str(mem_name)+","+str(mem_cpi)+"$#"

    def addPrefList(self, pref_string, project_dict):
        this_user_order = list(map(project_dict.get,[i.split("_")[1] for i in pref_string]))
        self.pref_order = "$#".join(this_user_order)        

    def __repr__(self): 
        return "<Reg. {}> <Name: {}>".format(self.username,self.name)
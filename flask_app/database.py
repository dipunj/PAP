from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
from config import Config
app = Flask(__name__)
app.config.from_object(Config)
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





    def __init__(self, username, password, name, cpi, group_size, **kwargs): 
        super(User, self).__init__(**kwargs)
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



def initializeDB(db):
    
    # create all tables of db
    db.create_all()
    
    # add user admin
    admin = User(username="admin",password="admin", name="admin",cpi=10,group_size=1)
    student = User(username="20154061", password="20154061",name="Dipunj",cpi=8.35,group_size=4)
    # add to session
    db.session.add(admin)
    db.session.add(student)
    db.session.commit()
    return db



def destroyDB(app):
    try:
        os.remove(app.config['SQLALCHEMY_DATABASE_URI'].split(':///')[1])
    except:
        pass
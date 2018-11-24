from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from config import Config
app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)



class User(db.Model): 
    # __tablename__ = 'users'

    username = db.Column(db.String(8),unique=True, primary_key=True, nullable=False)
    password = db.Column(db.String(80))
    name     = db.Column(db.String,nullable=False)
    cpi      = db.Column(db.Float,nullable=False)

    # after preferences has been submitted
    isPrefFinal = db.Column(db.Boolean,default=False)

    # set to true after user has entered details of all group members
    isGroupFinal = db.Column(db.Boolean,default=False)

    # login permission
    permission = db.Column(db.Boolean,nullable=False,default=True)
    # group size including 1st slotter
    group_size = db.Column(db.Integer,default=4)

    # seperator is $#@!
    all_member_string = db.Column(db.String)

    # seperator is $#@!
    pref_order = db.Column(db.String)





    def __init__(self, username, password, name, cpi, **kwargs): 
        super(User, self).__init__(**kwargs)
        self.username          = username
        self.password          = password
        self.name              = name
        self.cpi               = cpi
        self.all_member_string = "1,"+username+","+name+","+str(cpi)
        pass


    def addMember(self, group_position, mem_name,mem_cpi,mem_reg_no): 
        self.all_member_string += "$#@!"+str(group_position)+","+str(mem_reg_no)+","+str(mem_name)+","+str(mem_cpi)

    def getMembers(self):
        members = self.all_member_string.split('$#@!')
        printable_details = []
        for student in members:
            printable_details.append(tuple(student.split(',')))
        
        return printable_details

    def addPrefList(self, pref_order_list, academic_project_dict):
        """adds the preference order of the projects in academic_project_dict
        
        Args:
            pref_order_list (list): ["3","1","2"....]
            academic_project_dict (dict): {"1":"ML","2":"IOT".....}
        """

        this_user_order = list(map(academic_project_dict.get,pref_order_list))
        self.pref_order = "$#@!".join(this_user_order)        

    def getPrefList(self):
        to_dict = self.pref_order.split("$#@!")
        pref_dict = dict(enumerate(to_dict,start=1))
        pref_dict = {str(k):str(v) for k,v in pref_dict.items()}
        
        return pref_dict



class portalConfig(db.Model):

    mode = db.Column(db.Integer,primary_key=True)
    deadline = db.Column(db.DateTime,default=datetime(9999, 9, 9, 9, 9))
    reference_project_list = db.Column(db.String,default="")

    # 20154061$#@!20154015$#@!......
    reference_student_list = db.Column(db.String,default="")

    def __init__(self,mode):
        self.mode = mode
        pass

    
    def getcurrentProjectList(self):
        if not self.reference_project_list:
            return {}
        else:
            to_dict = self.reference_project_list.split("$#@!")
            pref_dict = dict(enumerate(to_dict,start=1))
            pref_dict = {str(k):str(v) for k,v in pref_dict.items()}
            return pref_dict

    def setProjectList(self, linear_list, project_dict):
        """sets the students in reference_project_list

        Args:
            linear_list (list): ["1","2","3"....]
            project_dict (dict): {"1":"suneeta@mnnit.ac.in__algo","2":"aks@mnnit.ac.in__DS".....}

        Result:
            self.pref_order == "$#@!suneeta__algo$#@!aks__DS"
        """

        project_name = list(map(project_dict.get,linear_list))
        self.reference_project_list = "$#@!".join(project_name)

    def getcurrentStudentList(self):
        if not self.reference_student_list:
            return {}
        else:
            to_dict = self.reference_student_list.split("$#@!")
            pref_dict = dict(enumerate(to_dict,start=1))
            pref_dict = {str(k):str(v) for k,v in pref_dict.items()}
            return pref_dict

    def setStudentList(self, linear_list, student_dict):
        """sets the students in reference_student_list

        Args:
            linear_list (list): ["1","2","3"....]
            student_dict (dict): {"1":"20154061","2":"20154015".....}

        Result:
            self.pref_order == "$#@!20154061$#@!20154015"
        """

        students_regno = list(map(student_dict.get,linear_list))
        self.reference_student_list = "$#@!".join(students_regno)



    def getDeadline(self):
        return (self.deadline.strftime('%B, %d %Y'),self.deadline.strftime('%I:%M %p IST'))



class Teacher(db.Model):
    
    # email id
    username = db.Column(db.String,primary_key=True,nullable=False)
    password = db.Column(db.String,nullable=False)
    name  = db.Column(db.String)
    isPrefFinal = db.Column(db.Boolean,default=False)
    myprojects = db.Column(db.String,default="")
    pref_order = db.Column(db.String)

    def __init__(self, username, password, name,**kwargs): 
        super(Teacher, self).__init__(**kwargs)
        self.username             = username
        self.name                 = name
        self.password             = password
        pass


    def addPrefList(self, pref_order_list, student_dict):
        """adds the preference order of the students from student_dict
        
        Args:
            pref_order_list (list): ["3","1","2"....]
            student_dict (dict): {"1":"Dipunj Gupta","2":"Abhey Rana", "3":"Manmeet Singh".....}
        """

        this_user_order = list(map(student_dict.get,pref_order_list))
        self.pref_order = "$#@!".join(this_user_order)        

    def getPrefList(self):
        to_dict = self.pref_order.split("$#@!")
        pref_dict = dict(enumerate(to_dict,start=1))
        pref_dict = {str(k):str(v) for k,v in pref_dict.items()}
        
        return pref_dict

    def setProjectList(self,prj_list):
        self.myprojects = "$#@!".join(prj_list)

    def getProjectList(self):
        return self.myprojects.split("$#@!")

def initializeDB(db):
    
    # create all tables of db
    db.create_all()
    
    # add user admin
    admin = User(username="admin",password="admin", name="admin",cpi=10)
    config = portalConfig(1)
    student = User(username="20154061", password="20154061",name="Dipunj",cpi=8.35)
    demo_teacher = Teacher(username="a@b.com",password="000",name="Prof. Suneeta")

    config.setStudentList(["1"],{"1":"20154061"})
    config.setProjectList(["1"],{"1":"Prof. Suneeta__algo"})
    
    # add to session
    db.session.add(config)
    db.session.add(demo_teacher)
    db.session.add(admin)
    db.session.add(student)
    db.session.commit()
    return db


def destroyDB(app):
    try:
        os.remove(app.config['SQLALCHEMY_DATABASE_URI'].split(':///')[1])
    except:
        pass
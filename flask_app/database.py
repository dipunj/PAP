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
    requests = db.Column(db.String,default="")
    
    leader = db.Column(db.String)

    # admin's slot = 0
    myslot = db.Column(db.Integer,nullable=False)

    # set to  after user's group leader/members is/are final
    # 1. req_notsent -> member : has not made a decision on any possible request, leader : has not sent any request
    # 2. reqsent     -> member : has accepted a request, but group is not yet finalised, leader : has sent request, but group not final, because one or more of the member is yet to accept request
    # 3. final       -> member,leader : groups are finalised
    isGroupFinal = db.Column(db.String,default="req_notsent")


    ##########################################
    # below is only for first slotter
    ##########################################

    # after preferences has been submitted
    isPrefFinal = db.Column(db.Boolean)

    # group size including 1st slotter, ensure group size,remaining_reqs is set whenever a new group leader is created
    group_size = db.Column(db.Integer)
    remaining_reqs = db.Column(db.String,default="")
    # seperator is $#@!
    all_member_string = db.Column(db.String)

    # seperator is $#@!
    pref_order = db.Column(db.String)

    Mentor = db.Column(db.String)





    def __init__(self, username, password, name, cpi, slot,**kwargs): 
        super(User, self).__init__(**kwargs)
        self.username          = username
        self.password          = password
        self.name              = name
        self.cpi               = cpi
        self.myslot            = slot
        self.all_member_string = str(slot)+","+username+","+name+","+str(cpi)
        pass


    # group leader's accepted member group list


    def resetMemberList(self):
        self.all_member_string = "1,"+self.username+","+self.name+","+str(self.cpi)

    def addMember(self, slot, mem_name,mem_cpi,mem_reg_no): 
        self.all_member_string += "$#@!"+str(slot)+","+str(mem_reg_no)+","+str(mem_name)+","+str(mem_cpi)

    def deleteMember(self,mem_reg_no):
        mymembers = self.getMembers()

        mems_reg = [i[1] for i in mymembers]
        if mem_reg_no in mems_reg:
            self.all_member_string = "$#@!".join([",".join(i) for i in mymembers if i[1] != mem_reg_no])


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



    # group member's pending request list

    def resetRequestList(self):
        self.requests = ""

    def addRequest(self,leader_regno):
        curr_reqs = set(self.getRequests())
        if curr_reqs == {''}:
            curr_reqs = set([leader_regno])
        else:
            curr_reqs.add(leader_regno)
        
        self.requests = '$#@!'.join(curr_reqs)
    
    def deleteRequest(self,leader_regno):
        curr_reqs = set(self.getRequests())
        if curr_reqs != {''}:
            curr_reqs = set(curr_reqs)
            curr_reqs.remove(leader_regno)

            self.requests = '$#@!'.join(curr_reqs)


    def getRequests(self):
        return self.requests.split('$#@!')






    # group leader's remaining list

    def resetRemainingList(self):
        self.remaining_reqs = ""

    def addToRemainingList(self,mem_reg):
        curr_list = set(self.getRemainingList())
        if curr_list == {''}:
            curr_list = set([mem_reg])
        else:
            curr_list.add(mem_reg)

        self.remaining_reqs = '$#@!'.join(curr_list)

    def deleteFromRemainingList(self,mem_reg):
        curr_list = set(self.getRemainingList())
        if curr_list != {''}:
            curr_list = set(curr_list)
            curr_list.remove(mem_reg)
            self.remaining_reqs = '$#@!'.join(curr_list)


    def getRemainingList(self):
        return self.remaining_reqs.split('$#@!')





class portalConfig(db.Model):

    mode = db.Column(db.Integer,primary_key=True)
    deadline = db.Column(db.DateTime,default=datetime(9999, 9, 9, 9, 9))
    reference_project_list = db.Column(db.String,default="")
    switch = db.Column(db.Boolean,default=True)
    # 20154061$#@!20154015$#@!......
    reference_student_list = db.Column(db.String,default="")
    resultDeclared = db.Column(db.Boolean,default=False,nullable=False)
    max_group_size = db.Column(db.Integer,default=0)

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
    myprojects = db.Column(db.String,default="")
    pref_order = db.Column(db.String)
    myYearStudents = db.Column(db.String,default="")
    isPrefFinal = db.Column(db.Boolean,default=False,nullable=False)

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

    def addYearStudents(self, reg_no, project_name):
        curr = self.myYearStudents.split("$#@!")
        if curr == ['']:
            curr = []
        curr.append(reg_no+"__"+project_name)
        self.myYearStudents = "$#@!".join(curr)
    
    def getYearStudents(self):
        return [tuple(i.split('__')) for i in self.myYearStudents.split('$#@!')]



def initializeDB(db):
    
    # create all tables of db
    db.create_all()
    
    # add user admin
    admin = User(username="admin",password="admin", name="admin",cpi=10,slot=0)
    config = portalConfig(1)
    # demo_student = User(username="20154061", password="20154061",name="Dipunj",cpi=8.35)
    # demo_teacher = Teacher(username="suneeta@mnnit.ac.in",password="20154061",name="Prof. Suneeta Agarwal")
    # demo_teacher.setProjectList(['Image Processing'])
    # config.setStudentList(["1"],{"1":"20154061"})
    # config.setProjectList(["1"],{"1":"suneeta@mnnit.ac.in__Image Processing"})
    
    # add to session
    db.session.add(config)
    # db.session.add(demo_teacher)
    db.session.add(admin)
    # db.session.add(demo_student)
    db.session.commit()
    return db


def destroyDB(app):
    try:
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], 'students.csv'))
    except:
        pass

    try:
        os.remove(app.config['SQLALCHEMY_DATABASE_URI'].split(':///')[1])
    except:
        pass
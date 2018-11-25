import os, json
from flask import Flask, request, render_template, session, flash
from datetime import datetime


from config import Config
from main import getStableRelations
from utilities import stable
from database import db,User,Teacher,portalConfig,destroyDB,initializeDB


# project_list = \
# {
#     "1" : 'Artifical Intelligence',
#     "2" : 'Machine Learning',
#     "3" : 'BlockChain',
#     "4" : 'Web Development',
#     "5" : 'IOT Systems',
#     "6" : 'Algorithms'
# }


app = Flask(__name__)
app.config.from_object(Config)

destroyDB(app)
db = initializeDB(db)









"""Login/Logout Related Routes"""

@app.route('/', methods=['POST','GET'])
def home():
    """handles the homepage of users
        userObj (User, optional): Defaults to None. user Object
    
    Renders:
        template according to session cookie, usertype (admin or normal)
    """

    admin = User.query.filter_by(username='admin').first()
    deadline = portalConfig.query.get(1).getDeadline()

    reference_prj_dict = {}
    project_list = portalConfig.query.get(1).getcurrentProjectList()
    print(project_list)
    for idx,project in project_list.items():
        teacher_project = project.split("__")
        reference_prj_dict[idx] = (Teacher.query.get(teacher_project[0]).name,teacher_project[1])
    
    if not reference_prj_dict:
        reference_prj_dict = {"" : "No Projects Added Yet"}

    reference_student_list = {}
    student_list = portalConfig.query.get(1).getcurrentStudentList()

    for idx,reg_no in student_list.items():
        reference_student_list[idx] = User.query.filter_by(username=reg_no).first()

    if not reference_student_list: 
        reference_student_list[" "] = fakeUser()

    #####################
    # LOGIN LOGIC BELOW
    ####################
    
    
    # unauthenticated -> take to login page
    if 'authenticated' not in session or session['authenticated'] == False:
        return render_template('login.html')
    else:

        if session['isTeacher'] == True:
            usrObj = Teacher.query.filter_by(username=session['username']).first()
        else:
            usrObj = User.query.filter_by(username=session['username']).first()

        # admin
        if usrObj.username == "admin":
            users = User.query.order_by(User.username).filter(User.username !="admin").all()
            teachers = Teacher.query.all()
            return render_template("admin.html",
                                    DB_group_size       = usrObj.group_size,
                                    DB_user_list        = users,
                                    DB_teacher_list     = teachers,
                                    DB_current_projects = reference_prj_dict,
                                    curr_deadline       = deadline)
        else:

            # teacher
            if session['isTeacher'] == True:
                if usrObj.isPrefFinal == False:
                    return render_template("teacherpreference.html",
                                            name          = usrObj.name,
                                            student_list  = reference_student_list,
                                            DB_deadline=deadline)
                else:
                    return render_template("teacherresult.html",
                                            name=usrObj.name,
                                            my_proj_list=usrObj.getPrefList(),
                                            my_group_members=usrObj.getMembers(),
                                            DB_deadline=deadline)

            # student
            else:
                if usrObj.isGroupFinal == False:
                    return render_template("group.html",
                                            name=usrObj.name,
                                            my_group_size=usrObj.group_size,
                                            DB_deadline=deadline)

                elif usrObj.isPrefFinal == False:
                    return render_template("preference.html",
                                            name          = usrObj.name,
                                            project_list  = reference_prj_dict,
                                            DB_deadline=deadline)
                else:
                    return render_template("done.html",
                                            name=usrObj.name,
                                            my_proj_list=usrObj.getPrefList(),
                                            my_group_members=usrObj.getMembers(),
                                            DB_deadline=deadline)


@app.route('/login',methods=["POST"])
def do_login():
    """facilitates login from the login.html login page    
    """

    isTeacher = False

    # check if this_user is admin or normal user
    this_user = User.query.filter_by(username=request.form['username']).first()
    
    # is this_user is not student or admin then check teacher table
    if this_user is None:
        this_user = Teacher.query.filter_by(username=request.form['username']).first()
        isTeacher = True

    # if this_user is still none -> invalid user
    if this_user is not None:
        if this_user.password == request.form["password"]:
            session['authenticated'] = True
            session['username'] = this_user.username
            session['name'] = this_user.name
            session['isTeacher'] = isTeacher
            try:
                session['cpi'] = this_user.cpi
                session['grp_size'] = this_user.group_size
            except:
                pass
        else:
            flash("Incorrect Password, Please Try Again")    
    else:
        flash("Invalid Username, Please Try Again")
    return home()


@app.route('/logout', methods=['POST'])
def do_logout():
    """facilitates logout from anywhere
       sets session cookie's authenticated to false
    """

    session['authenticated'] = False
    session['username']      = None
    session['name']          = None
    session['cpi']           = None
    session['grp_size']      = None

    return home()











"""Admin Page Routes"""



@app.route('/computeResult', methods=['POST'])
def autoCompute():

    # step 1 : generate dict containing student's preference
    student_pref = {}
    teacher_pref = {}

    grp_leaders = User.query.order_by(User.username).all()
    teachers    = Teachers.query.order_by(Teacher.email).all()

    if len(grp_leaders -1  != teachers):
        # error cannot procede
        pass


    for usrObj in grp_leaders:
        student_pref[usrObj.username] = usrObj.getPrefList().values()
    
    for prof in teachers:
        teacher_pref[prof.email] = prof.getPrefList().values()
        
    # step 2 : generate dict containing teacher's preferences

    myresult = stable(student_pref,teacher_pref)
    return render_template('result.html', result=myresult)

@app.route('/submit', methods=['POST'])
def doComputation():
    """main application logic
    
        uses stable marriage problem logic to assign projects in a stable manner
    """
    
    if request.files['teacher'] and request.files['student'] and request.files['members']:
    
        f = request.files['teacher']
        target_women = os.path.join(app.config['UPLOAD_FOLDER'],'women.json')
        f.save(target_women)

        f = request.files['student']
        target_men = os.path.join(app.config['UPLOAD_FOLDER'],'men.json')
        f.save(target_men)
        
        f = request.files['members']
        target_members = os.path.join(app.config['UPLOAD_FOLDER'],'members.json')
        f.save(target_members)
        
        myresult = getStableRelations(target_men,target_women)
        with open(target_members) as f:
            mystudent = json.load(f)
        
        return render_template('result.html', result=myresult, students=mystudent)
    else:
        return '<script>alert("Invalid Submission, Please Try Again")</script>'

@app.route('/result',methods=['POST'])
def result():
    if request.form['home'] == True:
        return home()


@app.route('/createUser', methods=['POST'])
def addUserToDB():
    """Adds the user from the form to database
    """

    global db
    
    name = request.form['newUserFullName']
    cgpa = request.form['newUserCGPA']
    reg_n = request.form['newUserRegNo']
    grp_size = request.form['newUserGroupSize']

    leader = User(username=reg_n, password=str(cgpa),name=name,cpi=cgpa,group_size=grp_size)

    db.session.add(leader)

    addTo_StudentRefList(reg_n)
    db.session.commit()


    return home()

def addTo_StudentRefList(user_regno):
    
    global db

    portal_config = portalConfig.query.get(1)

    student_dict = portal_config.getcurrentStudentList()
    student_list = list(student_dict.values())
    student_list.append(user_regno)
    new_dict = dict(enumerate(student_list,start=1))

    rank_list = []
    for i in range(1,len(new_dict)+1):
        rank_list.append(i)

    portal_config.setStudentList(rank_list, new_dict)
    db.session.commit()



@app.route('/deleteUser', methods=['POST'])
def delUserfromDB():
    
    global db

    if request.form['oldUserRegNo']:
        reg_no = request.form['oldUserRegNo']
        this_user = User.query.filter_by(username=reg_no).first()
        
        deleteFrm_StudentRefList(reg_no)
        
        db.session.delete(this_user)
        db.session.commit()

    return home()

def deleteFrm_StudentRefList(user_regno):

    global db

    portal_config = portalConfig.query.get(1)

    student_dict = portal_config.getcurrentStudentList()
    new_dict = { k:v for k, v in student_dict.items() if v != user_regno }
    
    rank_list = []
    for i in range(1,len(new_dict)+1):
        rank_list.append(str(i))
    
    portal_config.setStudentList(rank_list,new_dict)
    db.session.commit()




@app.route('/createTeacher', methods=['POST'])
def createTeacher_and_projects():

    global db
    
    teacher_name = request.form['teacher_fullname']
    teacher_email = request.form['teacher_username']
    
    new_teacher = Teacher(teacher_email,request.form['teacher_password'],teacher_name)
    
    projects = request.form['projectList'].strip().split("\r\n")
    new_teacher.setProjectList(projects)
    
    projects = [teacher_email+"__"+i for i in projects]
    db.session.add(new_teacher)
    
    for prj in projects:
        addTo_ProjRefList(prj)
    
    db.session.commit()
    
    return home()

def addTo_ProjRefList(project_name):
    
    global db

    portal_config = portalConfig.query.get(1)

    project_dict = portal_config.getcurrentProjectList()
    project_list = list(project_dict.values())
    project_list.append(project_name)
    new_dict = dict(enumerate(project_list,start=1))

    rank_list = []
    for i in range(1,len(new_dict)+1):
        rank_list.append(i)

    portal_config.setProjectList(rank_list, new_dict)
    db.session.commit()



@app.route('/deleteTeacher',methods=['POST'])
def deleteTeacher_and_projects():
    
    global db

    if request.form['teacher_username']:
        teacher_email = request.form['teacher_username']
        this_teacher = Teacher.query.filter_by(username=teacher_email).first()
        
        for prj in this_teacher.getProjectList():
            deleteFrm_ProjectList(teacher_email+"__"+prj)
        
        db.session.delete(this_teacher)
        db.session.commit()

    return home()


def deleteFrm_ProjectList(project_name):
    
    global db

    portal_config = portalConfig.query.get(1)

    project_dict = portal_config.getcurrentProjectList()
    new_dict = { k:v for k, v in project_dict.items() if v != project_name }
    
    rank_list = []
    for i in range(1,len(new_dict)+1):
        rank_list.append(str(i))
    
    portal_config.setProjectList(rank_list,new_dict)
    db.session.commit()




@app.route('/togglePortal', methods=['POST'])
def togglePortal():

    global db

    if request.form['portalSwitch'] == 'off':
        User.query.update({User.permission: False}) 
    else:
        User.query.update({User.permission: True}) 

    admin = User.query.filter_by(username='admin').first()
    admin.permission = True
    db.session.commit()

    return home()


@app.route('/setGroupSize', methods=['POST'])
def setGroupSize():

    global db

    admin=User.query.filter_by(username='admin').first()

    admin.group_size=request.form['defaultGrpSize']
    db.session.commit()

    return home()


@app.route('/setAdminPassword', methods=['POST'])
def setAdminPassword():

    global db

    new_pass = request.form['newPass']
    re_pass = request.form['confNewPass']

    admin = User.query.filter_by(username='admin').first()
    if new_pass == re_pass:
        admin.password = new_pass
        db.session.commit()

    return home()

@app.route('/setDeadline', methods=['POST'])
def setDeadline():

    config = portalConfig.query.get(1)
    print(request.form)
    config.deadline = datetime.strptime(request.form['new_deadline'], '%Y-%m-%dT%H:%M')
    db.session.commit()
    return home()


@app.route('/resetPortal',methods=['POST'])
def reset():

    global db
    global app

    if request.form['resetDATABASE'] == "true":
        User.query.delete()
        portalConfig.query.delete()
    
    db = initializeDB(db)
    
    return do_logout()


@app.route('/setProjectList', methods=['POST'])
def setProjects():

    global db
    if request.form['projectList']:
        
        projects = request.form['projectList'].strip().split("\r\n")

        ref_dict = {}
        linear_keys = []

        for idx,name in enumerate(projects,start=1):
            ref_dict.update({str(idx):name})
            linear_keys.append(str(idx))

        admin = User.query.filter_by(username="admin").first()
        
        admin.addPrefList(linear_keys,ref_dict)

        db.session.commit()

    return home()


@app.route('/resetProjectList', methods=['POST'])
def resetProjectList():

    global db

    admin = User.query.filter_by(username="admin").first()
    admin.pref_order = None
    db.session.commit()

    return home()











"""User Page Routes"""



@app.route('/ConfirmSubmission', methods=['POST'])
def confirmIt():

    admin = User.query.filter_by(username='admin').first()
    config = portalConfig.query.get(1)

    try:
        project_list = admin.getPrefList()
    except:
        project_list = {"" : "No Projects Added Yet"}

    pref_order = request.form['order'].split(",")
    pref_order = [i.split("_")[1] for i in pref_order]    
    
    preview = []

    for pr_id in pref_order:
        preview.append(project_list[pr_id])

    if pref_order == ['']:
        return home()
    else:
        return render_template("confirm.html",
                                name=session['name'],
                                confirm_list=preview,
                                prefOrder="-".join(pref_order),
                                DB_deadline=config.getDeadline())


@app.route('/finalSubmit',methods=['POST'])
def finalSubmit():

    global db

    if request.form['final_preference']:

        usrObj = User.query.filter_by(username=session['username']).first()
        admin = User.query.filter_by(username="admin").first()

        final_pref = request.form['final_preference'].split('-')
        usrObj.addPrefList(final_pref,admin.getPrefList())

        usrObj.isPrefFinal = True
        db.session.commit()
    
    return home()


@app.route('/selectMembers',methods=['POST'])
def selectMembers():

    global db
    
    usrObj = User.query.filter_by(username=session['username']).first()
    admin = User.query.filter_by(username="admin").first()

    user_grp_size = usrObj.group_size

    print(request.form)
    for i in range(2,user_grp_size+1):
        mem_name = request.form[str(i)+"_fullname"]
        mem_reg = request.form[str(i)+"_regno"]
        mem_cgpa = request.form[str(i)+"_cgpa"]
        usrObj.addMember(str(i),mem_name,mem_cgpa,mem_reg)
    
    usrObj.isGroupFinal = True
    db.session.commit()

    return home()





""" Teacher Page Routes"""

@app.route('/ConfirmSubmissionTeacher', methods=['POST'])
def confirmStudents():

    config = portalConfig.query.get(1)
    
    try:
        student_list = config.getcurrentStudentList()
    except:
        student_list = {"" : "No ProjStudents Added By Admin Yet"}

    pref_order = request.form['order'].split(",")
    pref_order = [i.split("_")[1] for i in pref_order]    
    
    preview = []

    for pr_id in pref_order:
        this_mem_reg_no = student_list[pr_id]
        usrObj = User.query.filter_by(username=this_mem_reg_no).first()
        preview.append(usrObj)

    if pref_order == ['']:
        return home()
    else:
        return render_template("teacherconfirm.html",
                                name=session['name'],
                                confirm_list=preview,
                                prefOrder="-".join(pref_order),
                                DB_deadline=config.getDeadline())

@app.route('/finalSubmitTeacher', methods=['POST'])
def finalStudentSubmit():

    global db

    if request.form['final_preference']:

        usrObj = User.query.filter_by(username=session['username']).first()
        portal_conf = portalConfig.query.get(1)

        final_pref = request.form['final_preference'].split('-')
        usrObj.addPrefList(final_pref,portal_conf.getcurrentStudentList())

        usrObj.isPrefFinal = True
        db.session.commit()
    
    return home()




class fakeUser:

    username = None
    name = None
    cpi = None

    def __init__(self):
        self.username = "-1"
        self.name = "Admin has not yet added any users"
        self.cpi = ""

    def __repr__ (self):
        print("{} - {} - {} ".format(self.username,self.name,self.cpi))





if __name__ == "__main__":
    app.secret_key = os.urandom(12)
    app.run(debug=False, host='127.0.0.1', port=4000)
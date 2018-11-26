import os, json
from flask import Flask, request, render_template, session, flash,send_file
from datetime import datetime
import xlwt

import csv,random

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
    portal_conf = portalConfig.query.get(1)

    deadline = portal_conf.getDeadline()
    isDeclared = portal_conf.resultDeclared

    reference_prj_dict = {}
    project_list = portal_conf.getcurrentProjectList()

    for idx,project in project_list.items():
        teacher_project = project.split("__")
        # convert from email to name with teacher query
        reference_prj_dict[idx] = (Teacher.query.get(teacher_project[0]).name,teacher_project[1])
    
    if not reference_prj_dict:
        reference_prj_dict = {"" : ("No Projects Added","No faculty Added")}

    reference_student_list = {}
    student_list = portal_conf.getcurrentStudentList()

    for idx,reg_no in student_list.items():
        reference_student_list[idx] = User.query.filter_by(username=reg_no).first()

    if not reference_student_list: 
        reference_student_list[" "] = fakeUser()

    #####################
    # LOGIN LOGIC BELOW
    ####################
    
    
    # unauthenticated -> take to login page
    if 'authenticated' not in session or session['authenticated'] == False:
        session['authenticated'] = False
        return render_template('login.html')
    else:

        if session['isTeacher'] == True:
            usrObj = Teacher.query.filter_by(username=session['username']).first()
        else:
            usrObj = User.query.filter_by(username=session['username']).first()

        if portal_conf.switch == False and usrObj.username != "admin":
            session['authenticated'] = False
            flash('login disabled by admin')
            return render_template('login.html')
        # admin
        if usrObj.username == "admin":
            users = User.query.order_by(User.username).filter(User.username !="admin").all()
            teachers = Teacher.query.all()

            return render_template("admin.html",
                                    DB_group_size       = usrObj.group_size,
                                    DB_user_list        = users,
                                    DB_teacher_list     = teachers,
                                    DB_current_projects = reference_prj_dict,
                                    curr_deadline       = deadline,
                                    DB_result_declared  = isDeclared,
                                    WAS_AT              = session['wasAt'],
                                    login_status        = portal_conf.switch)
        else:

            # teacher
            if session['isTeacher'] == True:
                if usrObj.isPrefFinal == False:
                    return render_template("teacherpreference.html",
                                            name          = usrObj.name,
                                            student_list  = reference_student_list,
                                            DB_deadline   = deadline)
                else:

                    # optimise this ->store in DB if teacher has already confirmed preference
                    # why calculate it every time on login

                    mystudent_list = {}
                    student_list = usrObj.getPrefList()
                    for idx,reg_no in student_list.items():
                        mystudent_list[idx] = User.query.filter_by(username=reg_no).first()

                    my_group_result = []
                    if isDeclared:
                        my__result = usrObj.getYearStudents()
                        # my__result.remove(('',))

                        for i in my__result:
                            reg_no,proj_name = i
                            this_leader = User.query.get(reg_no)
                            dummy = fakeUser()
                            dummy.username = reg_no
                            dummy.name = this_leader.name
                            dummy.cpi = this_leader.cpi
                            dummy.members = this_leader.getMembers()
                            dummy.project_name = proj_name
                            my_group_result.append(dummy)
                    
                    return render_template("teacherresult.html",
                                            name=usrObj.name,
                                            student_list=mystudent_list,
                                            DB_deadline=deadline,
                                            result=my_group_result,
                                            DB_result_declared = isDeclared)

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
                    myproj_pref = []

                    for num,this_prj in usrObj.getPrefList().items():
                        mentor = this_prj.split("__")[0]
                        prj = this_prj.split("__")[1]
                        myproj_pref.append((num,Teacher.query.get(mentor).name,prj))

                    return render_template("studentresult.html",
                                            name=usrObj.name,
                                            my_proj_list=myproj_pref,
                                            my_group_members=usrObj.getMembers(),
                                            DB_deadline=deadline,
                                            usrObj=usrObj,
                                            DB_result_declared = isDeclared)


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
            if session['username'] == "admin":
                 session['wasAt'] = "manageusers"
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



@app.route('/uploadUsers',methods=['POST'])
def uploadUsers():

    session['wasAt'] = request.form['wasAt']
    global db

    num_groups = request.form['num_of_groups']

    f = request.files['upload_file']
    student_file = os.path.join(app.config['UPLOAD_FOLDER'],'students.csv')
    f.save(student_file)

    with open(student_file) as f:
        data = [tuple(line) for line in csv.reader(f)]

    num_students = len(data)
    
    # num of groups will be same as number of first slotters
    extra_students = num_students%num_groups
    print("extra_students",extra_students)

    group_size = num_students//num_groups
    
    for slot in range(1,group_size+1):
        this_slot = data[(slot-1)*group_size:slot*group_size]
        for student in this_slot:
            # 0 -> registeration num
            # 1 -> full name
            # 2 -> CPI
            this_user = User(username=str(student[0]),password=str(student[2]),name=str(student[1]),cpi=student[2],myslot=slot)
            db.session.add(this_user)

    db.session.commit()

    # set group size of each leader
    all_first_slotter = User.query.filter_by(slot=1)
    for leader in all_first_slotter:
        leader.group_size = group_size
        addTo_StudentRefList(leader.username)

    db.session.commit()


    if extra_students != 0:

        # find (extra students) number of first_slotters and alot them these extra_students        
        first_slotters = random.sample(User.query.filter_by(slot=1),num_students%num_groups)
        for leader in first_slotters:
            leader.slot = group_size+1
    
        db.session.commit()

    return home()



@app.route('/computeResult', methods=['POST'])
def autoCompute():

    session['wasAt'] = request.form['wasAt']

    global db

    student_pref = {}
    teacher_pref = {}
    portal_conf = portalConfig.query.get(1)

    all_usrObj = User.query.order_by(User.username).filter(User.username !="admin").all()
    all_profs = Teacher.query.order_by(Teacher.username).all()

    all_projects = portal_conf.getcurrentProjectList()
    all_students = portal_conf.getcurrentStudentList()

    num_projects = len(all_projects)
    num_students = len(all_students)
    
    if num_projects != num_students:
        if num_projects < num_students:
            flash('Please add more projects! There are not enough projects for all groups','warning')
        else:
            flash('Number of projects are more than number of groups, cannot proceed','warning')
        return home()
    

    if not ifAllSubmitted():
        flash('Not all teachers and users have submitted','danger')
        return home()


    # step 1 : generate dict containing student's preference
    for usrObj in all_usrObj:
        student_pref[usrObj.username] = list(usrObj.getPrefList().values())
    
    # step 2 : generate dict containing teacher's preferences
    for prof in all_profs:
        for prj_underProf in prof.getProjectList():
            teacher_pref[prof.username+"__"+prj_underProf] = list(prof.getPrefList().values())
        


    ###########################################
    # MAIN APPLICATION LOGIC

    myresult = stable(student_pref,teacher_pref)
    
    ###########################################

    # initialise with empty string, on every computation
    for teacher in Teacher.query.all():
        teacher.myYearStudents = ""
    
    db.session.commit()

    for (reg_no,prj_name) in myresult:
        
        teacher_key = prj_name.split('__')[0]
        only_project_name = prj_name.split('__')[1]

        teacher = Teacher.query.get(teacher_key)
        userObj = User.query.get(reg_no)

        userObj.Mentor = teacher.name+"__"+only_project_name
        teacher.addYearStudents(reg_no,only_project_name)
    
    portal_conf.resultDeclared = True
    db.session.commit()

    flash('Result compute, check result page','success')
    return home()


def ifAllSubmitted():

    candidates = User.query.filter(User.username != "admin").all()
    candidates += Teacher.query.all()

    for obj in candidates:
        if not obj.isPrefFinal:
            return False
    
    return True



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


# @app.route('/createUser', methods=['POST'])
# def addUserToDB():
    """Adds the user from the form to database
    """

    session['wasAt'] = request.form['wasAt']

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



# @app.route('/deleteUser', methods=['POST'])
# def delUserfromDB():

#     session['wasAt'] = request.form['wasAt']
    
#     global db

#     if request.form['oldUserRegNo']:
#         reg_no = request.form['oldUserRegNo']
#         this_user = User.query.filter_by(username=reg_no).first()

#         if this_user is None or this_user.username == "admin":
#             flash('User does not exist in database','user')
#             return home()
        

#         deleteFrm_StudentRefList(reg_no)
#         db.session.delete(this_user)
            
#         db.session.commit()

#     return home()

# def deleteFrm_StudentRefList(user_regno):

#     global db

#     portal_config = portalConfig.query.get(1)

#     student_dict = portal_config.getcurrentStudentList()
#     student_dict = list(student_dict.values())
#     student_dict.remove(user_regno)
#     new_dict = dict(enumerate(student_dict,start=1))
#     new_dict = {str(k):str(v) for k,v in new_dict.items()}

#     rank_list = []
#     for i in range(1,len(new_dict)+1):
#         rank_list.append(str(i))
    
#     portal_config.setStudentList(rank_list,new_dict)
#     db.session.commit()







@app.route('/createTeacher', methods=['POST'])
def createTeacher_and_projects():

    session['wasAt'] = request.form['wasAt']

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

    session['wasAt'] = request.form['wasAt']
    
    global db

    if request.form['teacher_username']:
        teacher_email = request.form['teacher_username']
        this_teacher = Teacher.query.filter_by(username=teacher_email).first()
        
        if this_teacher is None:
            flash('Teacher does not exist in database','teacher')
            return home()

        for prj in this_teacher.getProjectList():
            deleteFrm_ProjectList(teacher_email+"__"+prj)
        
        db.session.delete(this_teacher)
        db.session.commit()

    return home()

def deleteFrm_ProjectList(project_name):
    
    global db

    portal_config = portalConfig.query.get(1)

    project_dict = portal_config.getcurrentProjectList()
    project_dict = list(project_dict.values())
    project_dict.remove(project_name)
    new_dict = dict(enumerate(project_dict,start=1))
    new_dict = {str(k):str(v) for k,v in new_dict.items()}

    rank_list = []
    for i in range(1,len(new_dict)+1):
        rank_list.append(str(i))
    portal_config.setProjectList(rank_list,new_dict)
    db.session.commit()







@app.route('/togglePortal', methods=['POST'])
def togglePortal():

    session['wasAt'] = request.form['wasAt']

    global db

    if request.form['portalSwitch'] == 'off':
        portalConfig.query.get(1).switch = False
    else:
        portalConfig.query.get(1).switch = True

    db.session.commit()

    return home()


@app.route('/setAdminPassword', methods=['POST'])
def setAdminPassword():

    session['wasAt'] = request.form['wasAt']

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

    session['wasAt'] = request.form['wasAt']

    config = portalConfig.query.get(1)

    config.deadline = datetime.strptime(request.form['new_deadline'], '%Y-%m-%dT%H:%M')
    db.session.commit()
    return home()








@app.route('/resetPortal',methods=['POST'])
def reset():

    global db
    global app

    if request.form['resetDATABASE'] == "true":
        User.query.delete()
        Teacher.query.delete()
        portalConfig.query.delete()
    
    db = initializeDB(db)
    
    return do_logout()

@app.route('/resetStudentList', methods=['POST'])
def resetStudentList():

    session['wasAt'] = request.form['wasAt']

    global db

    User.query.filter(User.username !="admin").delete()
    portalConfig.query.get(1).reference_student_list = ""
    db.session.commit()

    return home()

@app.route('/resetProjectList', methods=['POST'])
def resetProjectList():

    session['wasAt'] = request.form['wasAt']

    global db

    Teacher.query.delete()
    portalConfig.query.get(1).reference_project_list = ""
    db.session.commit()

    return home()











"""User Page Routes"""


@app.route('/ConfirmSubmission', methods=['POST'])
def confirmIt():

    config = portalConfig.query.get(1)

    try:
        project_list = config.getcurrentProjectList()
    except:
        project_list = {"" : "No Projects Added Yet"}

    pref_order = request.form['order'].split(",")
    pref_order = [i.split("_")[1] for i in pref_order]    
    
    preview = []

    for pr_id in pref_order:
        mentor = project_list[pr_id].split("__")[0]
        prj = project_list[pr_id].split("__")[1]
        preview.append((Teacher.query.get(mentor).name,prj))

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
        portal_config = portalConfig.query.get(1)
        
        final_pref = request.form['final_preference'].split('-')
        usrObj.addPrefList(final_pref,portal_config.getcurrentProjectList())

        usrObj.isPrefFinal = True
        db.session.commit()
    
    return home()


@app.route('/selectMembers',methods=['POST'])
def selectMembers():

    global db
    
    usrObj = User.query.filter_by(username=session['username']).first()
    admin = User.query.filter_by(username="admin").first()

    user_grp_size = usrObj.group_size

    for i in range(2,user_grp_size+1):
        mem_name = request.form[str(i)+"_fullname"]
        mem_reg = request.form[str(i)+"_regno"]
        mem_cgpa = request.form[str(i)+"_cgpa"]
        usrObj.addMember(str(i),mem_name,mem_cgpa,mem_reg)
    
    usrObj.isGroupFinal = True
    db.session.commit()

    return home()

@app.route('/setPassword', methods=['POST'])
def setUserPassword():

    global db

    new_pass = request.form['newPass']
    re_pass = request.form['confNewPass']
    old_pass = request.form['oldPass']

    if session['isTeacher']:
        usrObj = Teacher.query.get(session['username'])
    else:
        usrObj = User.query.get(session['username'])
    
    if old_pass != usrObj.password:
        return '<script>alert("Incorrect old password, Please Try Again")</script>'
    
    if new_pass == re_pass:
        usrObj.password = new_pass
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

        teacherObj = Teacher.query.filter_by(username=session['username']).first()
        portal_conf = portalConfig.query.get(1)

        final_pref = request.form['final_preference'].split('-')
        teacherObj.addPrefList(final_pref,portal_conf.getcurrentStudentList())

        teacherObj.isPrefFinal = True
        db.session.commit()
    
    return home()


@app.route('/getSheet',methods=['POST'])
def sendExcelSheet():

    teacher = Teacher.query.get(session['username'])
    workbook = xlwt.Workbook()
    sheets = {}
    bold = xlwt.easyxf('font: bold 1')

    for reg_no,prj in teacher.getYearStudents():
        xl = workbook.add_sheet(prj)

        # xl.write_merge(0,0,0,4,prj)

        xl.write(0,0,'S.No',bold)
        xl.write(0,1,'Reg.No',bold)
        xl.write(0,2,'NAME',bold)
        xl.write(0,3,'CGPA',bold)
        xl.write(0,4,'Grade',bold)
        
        members = User.query.get(reg_no).getMembers()
        for row,mem in enumerate(members,start=1):
            for i in range(4):
                xl.write(row,i,mem[i])

    workbook.save(os.path.join(app.config['UPLOAD_FOLDER'],teacher.username+".xls"))

    return send_file(os.path.join(app.config['UPLOAD_FOLDER'],teacher.username+".xls"),as_attachment=True,attachment_filename=teacher.name+".xls")



class fakeUser:

    username = None
    name = None
    cpi = None
    members = []
    project_name = ""

    def __init__(self):
        self.username = "-1"
        self.name = "Admin has not yet added any users"
        self.cpi = ""

    def __repr__ (self):
        print("{} - {} - {} ".format(self.username,self.name,self.cpi))





if __name__ == "__main__":
    app.secret_key = os.urandom(12)
    app.run(debug=False, host='127.0.0.1', port=4001)
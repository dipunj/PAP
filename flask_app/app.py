import os, json
from flask import Flask, request, render_template, session, flash,send_file
from datetime import datetime
import xlwt

import csv,random,operator

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

    global db
    
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
            first_slotters = User.query.order_by(User.cpi.desc()).filter((User.username !="admin") & (User.myslot == 1)).all()
            users = User.query.order_by(User.cpi.desc()).filter(User.username !="admin").all()
            teachers = Teacher.query.all()

            return render_template("admin.html",
                                    DB_group_size       = usrObj.group_size,
                                    DB_user_list        = users,
                                    num_of_slots        = portal_conf.max_group_size,
                                    DB_leader_list      = first_slotters,
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

                # normal member
                if usrObj.myslot != 1:
                    myrequests = []
                    try:
                        here_ldrs = usrObj.getRequests()
                        if here_ldrs != ['']:
                            for ldr_reg in here_ldrs:
                                ldr_obj = User.query.get(ldr_reg)
                                myrequests.append(ldr_obj)
                        else:
                            myrequests = None
                    except:
                        myrequests = None

                    if isDeclared == True:

                        leader = User.query.get(usrObj.leader)
                        myproj_pref = []

                        try:
                            for num,this_prj in leader.getPrefList().items():
                                mentor = this_prj.split("__")[0]
                                prj = this_prj.split("__")[1]
                                myproj_pref.append((num,Teacher.query.get(mentor).name,prj))
                        except:
                            pass

                        return render_template("studentresult.html",
                                                name=usrObj.name,
                                                my_proj_list=myproj_pref,
                                                my_group_members=leader.getMembers(),
                                                DB_deadline=deadline,
                                                usrObj=leader,
                                                DB_result_declared = isDeclared)
                    
                    if usrObj.isGroupFinal != "req_notsent":
                        leader = User.query.get(usrObj.leader)
                    else:
                        leader=None

                    if usrObj.isRejected == True:
                        usrObj.isRejected = False
                        db.session.commit()
                        flash(usrObj.reject_message)

                    try:
                        all_leaders = ",".join([usr.username for usr in myrequests ])
                    except:
                        all_leaders = ""
                    return render_template("groupMember.html",
                                                usrObj=usrObj,
                                                leader=leader,
                                                all_leaders=all_leaders,
                                                requests=myrequests,
                                                DB_deadline=deadline)
                # group leader
                else:
                    non_group_leaders = User.query.filter((User.myslot > 1) & (User.myslot < usrObj.group_size+1)).all()
                    if usrObj.isGroupFinal != "final":

                        slot_wise_members = {}

                        for slot in range(2,usrObj.group_size+1):
                            slot_wise_members[slot] = User.query.order_by(User.username).filter((User.username != "admin") & (User.myslot == slot) & (User.isGroupFinal != "final")).all()

                        my_pending_members = []
                        if usrObj.isGroupFinal == "reqsent":
                            current_members = usrObj.getRemainingList()
                            pending_members = [ member[1] for member in usrObj.getMembers() ]
                            
                            if current_members == [''] and pending_members == [usrObj.username]:
                                reg_tentative_members = []
                            else:
                                reg_tentative_members = current_members + pending_members
                                
                            for reg in reg_tentative_members:
                                my_pending_members.append(User.query.get(reg))

                            # implies total number of students == number of groups
                            if my_pending_members == []:
                                usrObj.isGroupFinal = "final"
                                usrObj.isPrefFinal = False
                                return home()

                            
                            my_pending_members.sort(key=lambda x: x.myslot)

                        if usrObj.isRejected == True:
                            usrObj.isRejected = False
                            db.session.commit()
                            flash(usrObj.reject_message)

                        return render_template("group.html",
                                                usrObj=usrObj,
                                                prospective_members=my_pending_members,
                                                all_students=non_group_leaders,
                                                this_slot_not_final=slot_wise_members,
                                                DB_deadline=deadline)

                    elif usrObj.isPrefFinal == False:
                        return render_template("preference.html",
                                                name          = usrObj.name,
                                                project_list  = reference_prj_dict,
                                                DB_deadline=deadline)
                    else:
                        myproj_pref = []

                        try:
                            for num,this_prj in usrObj.getPrefList().items():
                                mentor = this_prj.split("__")[0]
                                prj = this_prj.split("__")[1]
                                myproj_pref.append((num,Teacher.query.get(mentor).name,prj))
                        except:
                            pass

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

    num_groups = int(request.form['num_of_groups'])

    f = request.files['upload_file']
    student_file = os.path.join(app.config['UPLOAD_FOLDER'],'students.csv')
    
    try:
        os.remove(student_file)
    except:
        pass

    User.query.filter(User.username != "admin").delete()
    db.session.commit()

    f.save(student_file)
    reader = csv.reader(open(student_file), delimiter=",")
    data = sorted(reader, key=operator.itemgetter(2), reverse=True)
    num_students = len(data)
    


    # num of groups will be same as number of first slotters
    extra_students = num_students%num_groups

    group_size = num_students//num_groups
    portalConfig.query.get(1).max_group_size = group_size+(extra_students>0)

    # TODO : Put a check here if num_Groups > num_students

    if group_size > num_students:
        flash('Groups cannot be empty! Please reduce number of groups or increase number of students','upload_users')
        return home()

    for slot in range(1,group_size+(extra_students>0)+1):
        this_slot = data[(slot-1)*num_groups:slot*num_groups]
        for student in this_slot:
            # 0 -> registeration num
            # 1 -> full name
            # 2 -> CPI
            this_user = User(username=str(student[0]),password=str(student[2]),name=str(student[1]),cpi=student[2],slot=slot)
            db.session.add(this_user)

    db.session.commit()

    # set group size of each leader
    all_first_slotter = User.query.filter_by(myslot=1)
    for leader in all_first_slotter:
        leader.group_size = group_size
        addTo_StudentRefList(leader.username)

    db.session.commit()

    if extra_students != 0:
        # find (extra students) number of first_slotters and alot them these extra_students        

        # randomly
        # first_slotters = random.sample(User.query.filter_by(myslot=1).all(), extra_students)

        # top first slotters
        first_slotters = User.query.order_by(User.cpi.desc()).filter_by(myslot=1).all()[:extra_students]
        for leader in first_slotters:
            leader.group_size = group_size+1
    
        db.session.commit()

    return home()



@app.route('/computeResult', methods=['POST'])
def autoCompute():

    session['wasAt'] = request.form['wasAt']

    global db

    random_assgn = False
    student_pref = {}
    teacher_pref = {}
    portal_conf = portalConfig.query.get(1)

    all_usrObj = User.query.order_by(User.username).filter((User.username !="admin") & (User.myslot == 1)).all()
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
    

    # only affects those who have not made a preference
    random_assignment()

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

    if random_assgn == True:
        flash('Teachers and users who had not submitted thier preferences are being randomly assigning ','danger')
    else:
        flash('Result compute, check result page','success')
    return home()




def random_assignment():

    global db

    portal_conf = portalConfig.query.get(1)
    
    remaining_leaders = User.query.filter((User.myslot==1) & (User.isGroupFinal != "final")).all()

    # Step 1: Make groups out of remaining students
    for ldr_obj in remaining_leaders:    
        # reset this leader
        ldr_obj.resetMemberList()
        ldr_obj.resetRemainingList()
        ldr_obj.isRejected = False

        print("LEADER : ",ldr_obj.username,ldr_obj.group_size)
        for slot_num in range(2,ldr_obj.group_size+1):

            remaining_slotters = User.query.filter((User.myslot==slot_num) & (User.isGroupFinal != "final")).all()
            
            random_mem = random.choice(remaining_slotters)
            
            # reset member's group preference
            random_mem.resetRequestList()

            # add him to leader's Approved group
            ldr_obj.addMember(random_mem.myslot,random_mem.name,random_mem.cpi,random_mem.username)
            print(slot_num," : Setting",random_mem.username,"'s leader to:",ldr_obj.username)
            random_mem.leader = ldr_obj.username

            # set group status to final
            random_mem.isGroupFinal = "final"

        ldr_obj.isGroupFinal = "final"
        db.session.commit()
    

    # Step 2 : project preference randomly
    careless_leaders = User.query.filter_by(isPrefFinal=False).all()
    all_projects = portal_conf.getcurrentProjectList()

    for leader in careless_leaders:
        random_pref_order = list(all_projects.keys())
        random.shuffle(random_pref_order)
        leader.addPrefList(random_pref_order,all_projects)
        leader.isPrefFinal = True
        db.session.commit()

    # step 3: student preference teachers
    careless_teachers = Teacher.query.filter_by(isPrefFinal=False).all()
    all_students = portal_conf.getcurrentStudentList()

    for mentor in careless_teachers:
        random_pref_order = list(all_students.keys())
        random.shuffle(random_pref_order)
        mentor.addPrefList(random_pref_order,all_students)
        mentor.isPrefFinal = True
        db.session.commit()






def ifAllSubmitted():

    candidates = User.query.order_by(User.username).filter((User.username !="admin") & (User.myslot == 1)).all()
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






@app.route('/createTeacher', methods=['POST'])
def createTeacher_and_projects():

    session['wasAt'] = request.form['wasAt']

    global db

    submitted_members = User.query.filter((User.username != "admin")&(User.isPrefFinal == True)).all()
    if len(submitted_members) > 0:
        flash('Group Leaders have made a preference submission. It is now not possible to delete faculty members. Reset DataBase First','teacher')
        return home()


    teacher_name = request.form['teacher_fullname']
    teacher_email = request.form['teacher_username']

    if Teacher.query.filter_by(username=teacher_email).first() is not None:
        flash('Teacher already exists!','teacher')
        return home()

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

        submitted_members = User.query.filter((User.username != "admin")&(User.isPrefFinal == True)).all()

        if this_teacher is None:
            flash('Teacher does not exist in database','teacher')
            return home()

        if len(submitted_members) > 0:
            flash('Group Leaders have made a preference submission. It is now not possible to delete faculty membe. Reset DataBase First','teacher')
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

    members = User.query.filter((User.username != "admin") & (User.isPrefFinal == True)).all()

    if len(members) > 0:
        flash('Group Leaders have made a preference submission. It is not possible to delete projects now. Reset DataBase First','project_pref')
        return home()

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
    
    if pref_order == ['r_']:
        return home()

    pref_order = [i.split("_")[1] for i in pref_order]    
    
    preview = []

    for pr_id in pref_order:
        mentor = project_list[pr_id].split("__")[0]
        prj = project_list[pr_id].split("__")[1]
        preview.append((Teacher.query.get(mentor).name,prj))

    if pref_order == ['']:
        return home()
    else:
        usrObj = User.query.get(session['username'])
        return render_template("confirm.html",
                                usrObj=usrObj,
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
    leader = User.query.get(session['username'])

    user_grp_size = leader.group_size

    for slot_num in range(2,user_grp_size+1):
        mem_reg = request.form[str(slot_num)+"_regno"].split(" - ")[0]
        this_mem = User.query.get(mem_reg)

        # check if this_mem has made a decision?
        if this_mem.isGroupFinal == "req_notsent":
            this_mem.addRequest(leader.username)
            leader.addToRemainingList(this_mem.username)
        # if not, then is his group final?
        elif this_mem.isGroupFinal == "reqsent":

            # do not commit changes or change leader's isGroupFinal status 
            his_leader = User.query.get(this_mem.leader)
            flash(this_mem.name+"("+this_mem.username+") is under process of group formation with "+his_leader.name+"'s ")
            return home()
        else:

            # do not commit changes or change leader's isGroupFinal status
            his_leader = User.query.get(this_mem.leader)
            flash(this_mem.name+"("+this_mem.username+") Has already been finalized into"+his_leader.name+" ("+his_leader.username+")'s Group")
            return home()

    leader.isGroupFinal = "reqsent"
    db.session.commit()

    return home()



@app.route('/acceptLeader',methods=['POST'])
def acceptLeader():
    
    global db

    myleader = request.form['myleader']
    me = User.query.get(session['username'])

    other_leaders = []

    if myleader == "Reject All":

        me.isGroupFinal = "req_notsent"    
        other_leaders = request.form['all_leaders'].split(',')
        # step 1 : since me is rejecting all the requests, so set me's isGroupFinal status to req_notsent
        # step 2 : reset all the leaders which sent requested me        
        # step 3 : clear me's pending request list

    else:
        myleader_obj = User.query.get(myleader)

        accept_my_leader(myleader_obj,me)

        # step 6 : clear up any other requests that me has rejected by accepting myleader_obj's request
        # step 7 : clear me's request list
    
        # step 6
        other_leaders = me.getRequests()
        try:
            other_leaders.remove(myleader_obj.username)
        except:
            pass
    
    if other_leaders is None or other_leaders == ['']:
        other_leaders = []


    # step 2(if), step 6(else)
    clear_other_leaders(other_leaders, me)

    # step 3(if),step 7(else)
    me.resetRequestList()

    db.session.commit()
    return home()


def clear_other_leaders(other_leaders,me):

    global db

    for other_ldr in other_leaders:
        other_ldr_obj = User.query.get(other_ldr)

        # reset other_ldr

        # step 6.1: set isGroupFinal status to not sent
        # step 6.2: remove this leader from all members who had accepted his request
        # step 6.3: remove this leader from all members who have recieved his request but are yet to accept
        # step 6.4 : reset this leader group list
        # step 6.5 : reset this leader remaining member list


        # step 6.1
        other_ldr_obj.isGroupFinal = "req_notsent"
        other_ldr_obj.reject_message = me.name+" ("+me.username+") Has Rejected Group formation under your leadership. Please reform your group, after discussing with all of your propective members. Your Group is not yet finalised"
        other_ldr_obj.isRejected = True
        # step 6.2
        # me won't be here since me didn't accept other_ldr request
        acptd_peer_members = [i[1] for i in other_ldr_obj.getMembers()]
        for mem in acptd_peer_members:
            peer_member_obj = User.query.get(mem)
            peer_member_obj.leader = None
            peer_member_obj.isGroupFinal = "req_notsent"
            peer_member_obj.reject_message = me.name+" ("+me.username+") Has Rejected Group formation under "+other_ldr_obj.name+" ("+other_ldr_obj.username+")' Leadership. Your Group is not yet finalised"
            peer_member_obj.isRejected = True
        
        # step 6.3
        # me will be present here, so remove me from this list
        waiting_peer_members = other_ldr_obj.getRemainingList()
        try:
            waiting_peer_members.remove(me)
        except:
            pass
        for mem in waiting_peer_members:
            peer_member_obj = User.query.get(mem)
            peer_member_obj.deleteRequest(other_ldr_obj.username)
            

        # step 6.4
        other_ldr_obj.resetMemberList()
        
        # step 6.5
        other_ldr_obj.resetRemainingList()
        db.session.commit()


def accept_my_leader(myleader_obj,me):

    # step 1 : remove me from leader's Remaining group list 
    # step 2 : accept me to leader's group list
    # step 3 : set me's leader
    # step 4 : change me's isGroupFinal status to reqsent
    # step 5 : if me is the last one to accept in myleader_obj's list ->finalise/lock the group
    
    # step 1:        
    myleader_obj.deleteFromRemainingList(me.username)

    # step 2:
    myleader_obj.addMember(me.myslot,me.name,me.cpi,me.username)

    # step 3:
    me.leader = myleader_obj.username

    # step 4:
    me.isGroupFinal = "reqsent"

    # step 5:
    if myleader_obj.getRemainingList() == ['']:
        # me is the last final member to accept the request
        
        # finalise this group
        # step 5.1 : set myleader_obj's isGroupFinal to "final"
        # step 5.2 : for all members in group list, set isGroupFinal to "final"

        # step 5.1:
        myleader_obj.isGroupFinal = "final"
        myleader_obj.isPrefFinal = False
        # step 5.2
        acptd_peer_members = [i[1] for i in myleader_obj.getMembers()]
        for mem in acptd_peer_members:
            User.query.get(mem).isGroupFinal = "final"





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
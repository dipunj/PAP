import os, json
from flask import Flask, request, render_template, session, flash
from datetime import datetime


from config import Config
from main import getStableRelations
from database import db,User,destroyDB,initializeDB, portalConfig


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

    # destroyDB(app)
    # db = initializeDB(db)









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

    try:
        reference_prj_dict = admin.getPrefList()
    except:
        reference_prj_dict = {"" : "No Projects Added Yet"}

    if 'authenticated' not in session or session['authenticated'] == False:
        return render_template('login.html')
    else:
        usrObj = User.query.filter_by(username=session['username']).first()
        if usrObj.username == "admin":
            users = User.query.order_by(User.username).all()
            return render_template("admin.html",
                                    DB_group_size       = usrObj.group_size,
                                    DB_user_list        = users,
                                    DB_current_projects = reference_prj_dict,
                                    curr_deadline       = deadline)
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

    this_user = User.query.filter_by(username=request.form['username']).first()

    if this_user is not None:
        if this_user.password == request.form["password"]:
            session['authenticated'] = True
            session['username'] = this_user.username
            session['name'] = this_user.name
            session['cpi'] = this_user.cpi
            session['grp_size'] = this_user.group_size
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

    if (request.form['newUserFullName'] and request.form['newUserCGPA'] and request.form['newUserRegNo'] and request.form['newUserGroupSize']):

        name = request.form['newUserFullName']
        cgpa = request.form['newUserCGPA']
        reg_n = request.form['newUserRegNo']
        grp_size = request.form['newUserGroupSize']

        leader = User(username=reg_n, password=str(cgpa),name=name,cpi=cgpa,group_size=grp_size)
        db.session.add(leader)
        db.session.commit()

    return home()


@app.route('/deleteUser', methods=['POST'])
def delUserfromDB():
    
    global db

    if request.form['oldUserRegNo']:
        reg_no = request.form['oldUserRegNo']
        this_user = User.query.filter_by(username=reg_no).first()
        db.session.delete(this_user)
        db.session.commit()

    return home()


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

    admin=User.query.filter_by(username='admin').first()

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
        return render_template("confirm.html",name=session['name'], confirm_list=preview, prefOrder="-".join(pref_order))


@app.route('/finalSubmit',methods=['POST'])
def finalSubmit():

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














if __name__ == "__main__":
    app.secret_key = os.urandom(12)
    app.run(debug=False, host='127.0.0.1', port=4000)
import os, json
from config import Config
from flask import Flask, request, render_template, session, flash
from main import getStableRelations
from database import db,User,destroyDB,initializeDB



project_list = \
{
    "1" : 'Artifical Intelligence',
    "2" : 'Machine Learning',
    "3" : 'BlockChain',
    "4" : 'Web Development',
    "5" : 'IOT Systems',
    "6" : 'Algorithms'
}


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

    admin=User.query.filter_by(username='admin').first()

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
            return render_template("admin.html",DB_group_size=usrObj.group_size, DB_user_list=users, DB_current_projects=reference_prj_dict)
        else:
            return render_template("student.html", name=usrObj.name, project_list=reference_prj_dict, my_group_size=usrObj.group_size)


@app.route('/login',methods=["POST"])
def do_login():
    """facilitates login from the login.html login page    
    """

    this_user = User.query.filter_by(username=request.form['username']).first()

    if this_user is not None:
        if this_user.password == request.form["password"]:
            session['authenticated'] = True
            session['username'] = this_user.username
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
    session['usrObj'] = None

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


@app.route('/resetPortal',methods=['POST'])
def reset():

    global db
    global app

    if request.form['resetDATABASE'] == "true":
        User.query.delete()
    
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
            linear_keys.append("r_"+str(idx))

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
def confirmIt(project_list=project_list):

    order = request.form['order'].split(",")
    order = [i.split("_")[1] for i in order]    
    preview = []

    for pr_id in order:
        preview.append(project_list[pr_id])
        
    return render_template("confirm.html",name=session['name'], confirm_list=preview)



















if __name__ == "__main__":
    app.secret_key = os.urandom(12)
    app.run(debug=False, host='127.0.0.1', port=4000)
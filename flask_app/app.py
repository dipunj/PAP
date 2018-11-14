import os, json
from flask import Flask, request, render_template, session, flash
from main import getStableRelations
from database import db, User


app = Flask(__name__)
db.create_all()

admin = User(username="admin",password="mnnit123", name="admin")
student = User(username="20154061", password="20154061",name="Dipunj")
db.session.add(admin)
db.session.add(student)
db.session.commit()

# project_dir   = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(app.root_path, 'db/')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER






@app.route('/', methods=['POST','GET'])
def home(userObj=None):

    if userObj is None or session['logged_in'] == False:
        return render_template('login.html')
    else:
        if userObj.username == "admin":
            return render_template("admin.html")
        else:
            return render_template("student.html", name=userObj.name)


@app.route('/login',methods=["POST"])
def do_login():

    this_user = User.query.filter_by(username=request.form['username']).first()

    if this_user is not None:
        if this_user.password == request.form["password"]:
            session['logged_in'] = True
        else:
            flash("Incorrect Password, Please Try Again")    
    else:
        flash("Invalid Username, Please Try Again")
    
    return home(this_user)


@app.route('/logout', methods=['POST'])
def do_admin_logout():
    session['logged_in'] = False
    return home()





@app.route('/submit', methods=['POST'])
def doComputation():

    
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


if __name__ == "__main__":
    app.secret_key = os.urandom(12)
    app.run(debug=False, host='127.0.0.1', port=4000)
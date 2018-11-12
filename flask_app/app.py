from flask import Flask, request, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy
from main import getStableRelations
import os, json


app = Flask(__name__)

# project_dir   = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(app.root_path, 'db/')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

database_file = "sqlite:///{}".format(os.path.join(UPLOAD_FOLDER, "users.db"))
app.config["SQLALCHEMY_DATABASE_URI"] = database_file
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


print(database_file)
db = SQLAlchemy(app)

class user(db.Model):
    # __tablename__ = 'users'

    username = db.Column(db.String(8),unique=True, primary_key=True, nullable=False)
    password = db.Column(db.String(80))
    name = db.Column(db.String)
    group_position = db.Column(db.Integer,nullable=False)

    def __init__(self, username, password):
        self.username = username
        self.password = password

    def __repr__(self):
         return "<Reg. {}><Username: {}><Group : Position {}>".format(self.username,self.username,self.group_position)
        

db.create_all()

admin = user('admin', 'mnnit123')
db.session.add(admin)
db.session.commit()
guest = user('20154061', '20154061')
db.session.add(guest)
db.session.commit()












@app.route('/', methods=['POST','GET'])
def home(user_row=None):

    if user_row is None or session['logged_in'] == False:
        return render_template('login.html')
    else:
        if user_row.username == "admin":
            return render_template("admin.html")
        else:
            return render_template("student.html", name=user_row.name)


@app.route('/login',methods=["POST"])
def do_login():

    this_user = UserModel.query.filter_by(username=int(request.form['username'])).first()

    if this_user is not None:
        if this_user.password == request.form["password"]:
            session['logged_in'] = True
        else:
            flash("Incorrect Password, Please Try Again")    
    else:
        flash("Invalid Username, Please Try Again")
    
    return home(user_row)


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
    app.run(debug=False, host='0.0.0.0', port=4001)
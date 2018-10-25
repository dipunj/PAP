from flask import Flask, request, render_template, session
from main import getStableRelations
import os, json

app = Flask(__name__)

UPLOAD_FOLDER = os.path.join(app.root_path, 'db/')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def home():
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        return render_template('submit.html')




@app.route('/login', methods=['POST'])
def do_admin_login():
    if request.form['pass'] == 'mnnit123' and request.form['username'] == 'admin':
        session['logged_in'] = True
    else:
        return '<script>alert("Invalid Credentials, Please Try Again")</script>'
    return home()


@app.route('/submit', methods=['POST'])
def doComputation():
    if request.files['teacher'] and request.files['student']:
        
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
    if request.form['back'] == True:
        return home()


@app.route("/logout")
def logout():
    session['logged_in'] = False
    return home()


if __name__ == "__main__":
    app.secret_key = os.urandom(12)
    app.run(debug=False, host='0.0.0.0', port=4001)
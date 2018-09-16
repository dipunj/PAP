from flask import Flask, request, render_template
from main import getStableRelations
import os

app = Flask(__name__)

UPLOAD_FOLDER = os.path.join(app.root_path, 'db/')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def home():
    return render_template('submit.html')


@app.route('/submit', methods=['POST'])
def doComputation():
    if request.files['teacher'] and request.files['student']:
        
        f = request.files['teacher']
        target_women = os.path.join(app.config['UPLOAD_FOLDER'],'women.json')
        f.save(target_women)
        
        f = request.files['student']
        target_men = os.path.join(app.config['UPLOAD_FOLDER'],'men.json')
        f.save(target_men)

        result = getStableRelations(target_men,target_women)
        return render_template('result.html', result=result)
    else:
        return '<script>alert("Invalid Submission, Please Try Again")</script>'


if __name__ == "__main__":
    app.secret_key = os.urandom(12)
    app.run(debug=True, host='0.0.0.0', port=4000)
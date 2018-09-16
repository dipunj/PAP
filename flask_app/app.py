from utilities import *
from flask import *
from main import getStableRelations
import os

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('submit.html')


@app.route('/submit', methods=['POST'])
def doComputation():
    if request.files['teacher'] and request.files['student']:
        
        f = request.files['teacher']
        f.save('men.json')
        
        f = request.files['student']
        f.save('women.json')

        result = getStableRelations('men.json','women.json')
        return render_template('result.html', result=result)
    else:
        return '<script>alert("Invalid Submission, Please Try Again")</script>'


if __name__ == "__main__":
    app.secret_key = os.urandom(12)
    app.run(debug=True, host='0.0.0.0', port=4000)
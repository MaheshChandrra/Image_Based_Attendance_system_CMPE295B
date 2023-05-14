from flask import Flask, request, redirect, url_for, render_template
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required
import os
import zipfile
from werkzeug.utils import secure_filename
import shutil
import face_encoder
import face_recognition
import facial_recognition
from PIL import Image
from flask_login import current_user


app = Flask(__name__)
app.secret_key = '1234'

UPLOAD_FOLDER = 'Classes'
ALLOWED_EXTENSIONS = {'zip'}
GROUP_PICTURES='Group_Pictures'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['GROUP_PICTURES'] = GROUP_PICTURES

login_manager = LoginManager()
login_manager.init_app(app)

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, id):
        self.id = id

# In-memory user database for simplicity
users = {'admin@gmail.com': {'password': 'admin'}}

# User loader function for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template("login.html")

@app.route('/login', methods=['GET', 'POST'])
def login():

    print(request.form)
    multi_dict = request.args
    for key in multi_dict:
        print(multi_dict.get(key))
        print(multi_dict.getlist(key))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['login_password']

        if username in users and users[username]['password'] == password:
            user = User(username)
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error=True)
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    username = current_user.id  # get the current user's ID
    return render_template("dashboard.html", username=username)
    # return render_template("dashboard.html")


@app.route('/services', methods=['GET', 'POST'])
@login_required
def services():
    return render_template("services.html")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    if file and file.filename.endswith('.zip'): # Check if the uploaded file is a zipped file
        filename = secure_filename(file.filename)

        if filename.split('.')[0] in os.listdir(app.config['UPLOAD_FOLDER']):
            shutil.rmtree(os.path.join(app.config['UPLOAD_FOLDER'], filename.split('.')[0]))
        
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        with zipfile.ZipFile(os.path.join(app.config['UPLOAD_FOLDER'], filename), 'r') as zip_ref:
            zip_ref.extractall(os.path.join(app.config['UPLOAD_FOLDER']))


        if filename in os.listdir(app.config['UPLOAD_FOLDER']):
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        return redirect(url_for('uploaded_file', filename=filename))
    return 'Invalid file format. Please upload a zipped file.'


@app.route('/mark_attendance',methods=['GET', 'POST'])
@login_required
def mark_attendance():
    file = request.files['file']
    class_name = request.form['class_name']
    path = os.path.join(app.config['GROUP_PICTURES'], class_name)
    # Check whether the specified path exists or not
    isExist = os.path.exists(path)
    if not isExist:
        # Create a new directory because it does not exist
        os.makedirs(path)
    print("The new directory is created!")
    print(file.filename)
    print(class_name)
    

    group_picture_path=os.path.join(app.config['GROUP_PICTURES'], class_name,file.filename)
    file.save(group_picture_path)

    face_encoder.generate_face_encodings(class_name)
    persons=facial_recognition.perform_face_recognition(class_name,group_picture_path)

    return render_template('results.html', persons=persons)



@app.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    return f'''
    <!doctype html>
    <html>
    <body>
        <h1>Uploaded File</h1>
        <p>The file {filename} has been uploaded.</p>
    </body>
    </html>
    '''


@app.route('/viewclasses')
@login_required
def uploaded_file(filename):
    return f'''
    <!doctype html>
    <html>
    <body>
        <h1>Uploaded File</h1>
        <p>The file {filename} has been uploaded.</p>
    </body>
    </html>
    '''

if __name__ == '__main__':
    app.run(debug=True)

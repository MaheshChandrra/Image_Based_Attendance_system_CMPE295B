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
import os
from flask import Markup
from pymongo import MongoClient, UpdateOne
from init import class_totals_collection, attendance_collection, courses_collection

import pymongo
import pandas as pd
import plotly
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import json

app = Flask(__name__)
app.secret_key = '1234'

db_name = "attendance_system_db"
uri = "mongodb://localhost:27017"
client = MongoClient(uri)
db = client[db_name]

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

    # print(request.form)
    # multi_dict = request.args
    # for key in multi_dict:
    #     print(multi_dict.get(key))
    #     print(multi_dict.getlist(key))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        dbuser = db.users.find_one({"email": username})
        print(dbuser)

        if dbuser and dbuser['password'] == password:
            user = User(username)
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error=True)
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    return render_template('signup.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    print(request.form)
    # multi_dict = request.args
    # for key in multi_dict:
    #     print(multi_dict.get(key))
    #     print(multi_dict.getlist(key))
    if request.method == 'POST':
        row = {
            "firstName": request.form['firstName'],
            "lastName": request.form['lastName'],
            "email": request.form['email'],
            "professor_id": request.form['professor_id'],
            "username": request.form['username'],
            "password": request.form['password']
        }

        db.users.insert_one(row)
        # print(row)
    
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
    return render_template("dashboard.html", username=username, courses=get_courses())
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
    username = current_user.id
    file = request.files['file']
    USER_NAME=current_user.id.split("@")[0]
    CLASS_DIR=app.config['UPLOAD_FOLDER']+"/"+USER_NAME

    class_name = request.form['class_name']
    prof_name = request.form['prof_name']

    STATIC_DIR = "static/"+USER_NAME+"/"+class_name

    if not os.path.exists(CLASS_DIR):
        # Create a new directory because it does not exist
        os.makedirs(CLASS_DIR)
        print("[INFO] Directory Created:",CLASS_DIR)
    if file.filename == '':
        return redirect(request.url)
    if file and file.filename.endswith('.zip'): # Check if the uploaded file is a zipped file
        filename = secure_filename(file.filename)

        if filename.split('.')[0] in os.listdir(CLASS_DIR):
            shutil.rmtree(os.path.join(CLASS_DIR, filename.split('.')[0]))
        
        file.save(os.path.join(CLASS_DIR, filename))
        with zipfile.ZipFile(os.path.join(CLASS_DIR, filename), 'r') as zip_ref:
            zip_ref.extractall(os.path.join(CLASS_DIR))


        if filename in os.listdir(CLASS_DIR):
            os.remove(os.path.join(CLASS_DIR, filename))

        for student_info in os.listdir(os.path.join(CLASS_DIR,filename.split(".")[0])):
            courses_collection.update_one(
                {"name_professor_section": filename.split(".")[0]},
                {"$addToSet": {"students": '_'.join(student_info.split("_")[:2])}},
                upsert=True
            )

        shutil.copytree(CLASS_DIR+"/"+class_name, STATIC_DIR)
        shutil.copytree(CLASS_DIR+"/"+class_name, "static/images/"+class_name)

        # students = []
        # for filename in os.listdir(CLASS_DIR+"/"+class_name):
        #     student_name = filename.split(".")
        #     students.append(student_name[0])
        
        # db.courses.insert_one({"course_name": class_name, "students": students})

        # professor = db.professors.find_one({"email": username})
        # new_courses_list = professor["courses"]
        # new_courses_list.append(class_name)
        # db.professors.update_one({"email": username}, {"$set": {"courses": new_courses_list}})

        return redirect(url_for('uploaded_file', filename=filename))
    return 'Invalid file format. Please upload a zipped file.'


@app.route('/mark_attendance',methods=['GET', 'POST'])
@login_required
def mark_attendance():
    print("form---", request.form)
    file = request.files['file']
    class_name = request.form['class_name']
    current_date = request.form['date']

    print(class_name)
    USER_NAME=current_user.id.split("@")[0]
    GRP_DIR=app.config['GROUP_PICTURES']+"/"+USER_NAME
    USER_NAME=current_user.id.split("@")[0]
    CLASS_DIR=app.config['UPLOAD_FOLDER']+"/"+USER_NAME
    
    path = os.path.join(GRP_DIR, class_name)
    # Check whether the specified path exists or not
    isExist = os.path.exists(path)
    if not isExist:
        # Create a new directory because it does not exist
        os.makedirs(path)
    print("The new directory is created!")
    print(file.filename)
    print(class_name)
    

    group_picture_path=os.path.join(GRP_DIR, class_name,file.filename)
    file.save(group_picture_path)

    print(CLASS_DIR)

    face_encoder.generate_face_encodings(class_name,CLASS_DIR,USER_NAME)
    persons=facial_recognition.perform_face_recognition(class_name,group_picture_path,USER_NAME)

    student_name_set = set()
    for i in persons:
        student_name_set.add('_'.join(i['name'].split("_")[:2]))
    class_name_section = persons[0]['image'].split('/')[1]


    class_totals_collection.update_one(
        {"name_professor_section" : class_name_section},
        {"$addToSet": {"previous_dates": current_date}},
        upsert = True
    )


    course_document = courses_collection.find_one({"name_professor_section": class_name_section})

    student_set = course_document.get("students", set())

    print("1----", student_set)
    
    class_new_document = class_totals_collection.find_one({"name_professor_section": class_name_section})

    dates_set = class_new_document.get("previous_dates", set())
    if current_date not in dates_set:
        filter = {"name_professor_section": class_name_section}
        update = {"$inc": {"classes_number": 1}, "$addToSet": {"previous_dates": current_date}}
        class_totals_collection.update_one(filter, update)
    
    print("2----", student_name_set)

    for student in student_set:
        filter = {
                    "name_professor_section": class_name_section,
                    "StudentName_SID": student,
                    "AttendedDate": current_date,
                }
        if student in student_name_set:  
            update = {
                        "$set": {
                            "Status": "Present",
                        }
                    }
            
        else:
            update = {
                        "$set": {
                            "Status": "Absent",
                        }
                    }
        existing_record = attendance_collection.find_one(filter)
        if existing_record and existing_record['Status'] == 'Present':
            continue
        update_one = UpdateOne(filter, update, upsert=True)
        attendance_collection.bulk_write([update_one])

    # persons_set = set([person['name'] for person in persons])

    # students = db.courses.find_one({"name_professor_section": class_name})["students"]
    # persons_with_attendance = []
    # for student in students:
    #     display_name = '_'.join(student.split('_')[:2])
    #     attendance_status = False
    #     if student in persons_set:
    #         attendance_status = True
    #     db.attendance.insert_one({"student": student, "course_name": class_name, "attendance_status": attendance_status, "attendance_date": str(attendance_date)})
    #     persons_with_attendance.append({'name': student, 'display_name': display_name, 'image': class_name+"/"+student+".png", "attendance_status": attendance_status})
    
    # print('persons---', persons_with_attendance)


    # return render_template('results.html', persons=persons_with_attendance, username = current_user.id, attendance_date=current_date)
    return render_template("dashboard.html", username=current_user.id, courses=get_courses())



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
def viewclasses():

      # Set the directory path
    
    directory_path = app.config['UPLOAD_FOLDER']+"/"+current_user.id.split("@")[0]

    if not os.path.exists(directory_path):
        return render_template("view_classes.html",cards=[],username=current_user.id)
    
    if not os.path.exists("static/"+current_user.id.split("@")[0]+"/"):
        shutil.copytree(directory_path, "static/"+current_user.id.split("@")[0]+"/")

    # Get a list of all folders in the directory
    folders = os.listdir(directory_path)
    # Create an empty list to store the cards
    cards = []
    # Loop through each folder in the directory
    for folder in folders:
        # Set the folder path
        folder_path = os.path.join(directory_path, folder)
        # Get a list of all images in the folder
        images = os.listdir(folder_path)
        # Create a dictionary to store the folder name and images
        folder_data = {
            "display_name": folder,
            "name": current_user.id.split("@")[0]+"/"+folder,
            "images": images,
            "student": [i.split(".")[0] for i in images ],
        }
        attendace = db.attendance.find({"course_name": folder})
        for a in attendace:
            print(a['student']+"--"+('present' if a['attendance_status'] else 'Abscent'))
        # Add the folder data to the cards list
        cards.append(folder_data)
        print(cards)
    # Render the template with the cards
    return render_template("view_classes.html", cards=cards,username=current_user.id)



    
     # Get all the folders in the specified directory
    directory=app.config['UPLOAD_FOLDER']+"/"+current_user.id.split("@")[0]
    folders = [f for f in os.listdir(directory) if os.path.isdir(os.path.join(directory, f))]
    print(folders)
    # Generate a Bootstrap card for each folder
    cards_html = ""
    for folder in folders:
        # Get the path to the folder and the number of images it contains
        folder_path = os.path.join(directory, folder)
        num_images = len([f for f in os.listdir(folder_path) ])

        print(num_images)
        print(os.listdir(folder_path))
        
        # Generate the HTML for the Bootstrap card
        card_html = f'''
            <div class="card">
              <div class="card-body">
                <h5 class="card-title">{folder}</h5>
                <p class="card-text">{num_images} images</p>
                <button type="button" class="btn btn-primary" data-toggle="modal" data-target="#{folder}-modal">
                  View images
                </button>
              </div>
            </div>
        '''
        
        # Generate the HTML for the modal that displays the images
        modal_html = f'''
            <div class="modal fade" id="{folder}-modal" tabindex="-1" role="dialog" aria-labelledby="{folder}-modal-label" aria-hidden="true">
              <div class="modal-dialog modal-dialog-centered modal-lg" role="document">
                <div class="modal-content">
                  <div class="modal-header">
                    <h5 class="modal-title" id="{folder}-modal-label">{folder} images</h5>
                    <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                      <span aria-hidden="true">&times;</span>
                    </button>
                  </div>
                  <div class="modal-body">
                    <div class="row">
        '''
        
        # Add the HTML for each image in the folder
        for image in os.listdir(folder_path):
            if image.endswith('.jpg') or image.endswith('.png') or image.endswith('.PNG'):
                image_path = os.path.join(folder_path, image)
                image_path=image_path.replace("\\","/")
                modal_html += f'''
                    <div class="col-md-4">
                      <div class="card mb-4 shadow-sm">
                        <img src="{image_path}" class="card-img-top" alt="{image}">
                      </div>
                    </div>
                '''
        
        # Close the modal HTML
        modal_html += '''
                    </div>
                  </div>
                </div>
              </div>
            </div>
        '''
        
        # Add the card and modal HTML to the overall HTML
        cards_html += card_html + modal_html
    # card_html = """<div class="row">
    #                 """


    # folder_path=app.config['UPLOAD_FOLDER']+"/"+current_user.id.split("@")[0]


    # for filename in os.listdir(folder_path):

    #     total_students=len(os.listdir(folder_path+"/"+filename))
    #     card_html += f"""
    #             <div class="col-sm-6">
    #             <div class="card">
    #             <div class="card-body">
    #                 <h5 class="card-title">{filename}</h5>
    #                 <p class="card-text">This class contains a total of {total_students} student images</p>
    #                 <a href="#" class="btn btn-primary">View Students</a>
    #             </div>
    #             </div>
    #         </div>
    #         """
    # card_html=card_html+"</div>"
    # if card_html == "":
    #     card_html = "<p>No files found.</p>"
    return render_template("view_classes.html",classes_rendered_html=cards_html)

@app.route('/viewattendance', methods=['GET', 'POST'])
@login_required
def viewattendance():
    username = current_user.id
    # Define the name_professor_section to analyze
    name_professor_section = request.form['selected_course']

    # Create dataframe for total number of classes
    class_totals = list(class_totals_collection.find({"name_professor_section": name_professor_section}))
    
    if len(class_totals) == 0:
        return redirect(url_for('dashboard'))

    class_totals_df = pd.DataFrame(class_totals)
    class_totals_df = class_totals_df[["name_professor_section", "previous_dates"]]
    class_totals_df["previous_dates_len"] = class_totals_df["previous_dates"].apply(lambda x: len(x))
    class_totals_df = class_totals_df[["name_professor_section", "previous_dates_len"]]
    class_totals_df = class_totals_df.rename(columns={"previous_dates_len": "Total Number of Classes"})

    # Create dataframe for total number of students in the class
    courses = list(courses_collection.find({"name_professor_section": name_professor_section}))
    courses_df = pd.DataFrame(courses)
    courses_df = courses_df[["name_professor_section", "students"]]
    courses_df["Total Number of Students"] = courses_df["students"].apply(lambda x: len(x))
    courses_df = courses_df[["name_professor_section", "Total Number of Students"]]

    # Create dataframe for total attendees from the latest class
    attendance = list(attendance_collection.find({"name_professor_section": name_professor_section}))
    if len(attendance) == 0:
        return render_template('get_stats.html', noData='true', course=name_professor_section, username=current_user.id)
    attendance_df = pd.DataFrame(attendance)
    # attendance_df["AttendedDate"] = pd.to_datetime(attendance_df["AttendedDate"])
    latest_date = attendance_df["AttendedDate"].max()
    latest_attendance_df = attendance_df[attendance_df["AttendedDate"] == latest_date]
    latest_attendance_df = latest_attendance_df[latest_attendance_df["Status"] == 'Present']
    latest_attendance_df = latest_attendance_df.groupby("name_professor_section").agg({"StudentName_SID": "count"}).reset_index()
    latest_attendance_df = latest_attendance_df.rename(columns={"StudentName_SID": "Total Attendees"})
    courses_df["Total Attendees"] = latest_attendance_df["Total Attendees"]
    # courses_df["Attendance Rate"] = courses_df["Total Attendees"] / courses_df["Total Number of Students"]
    courses_df["Attendance Rate"] = courses_df["Total Attendees"] / len(attendance_df[attendance_df["AttendedDate"] == latest_date])
    total_number_of_students = len(attendance_df[attendance_df["AttendedDate"] == latest_date])
    # print("-------------", courses_df)

    # Create dataframe for number of attendees by date
    attendance_df = attendance_df.groupby(["name_professor_section", "AttendedDate"]).agg({"StudentName_SID": "count"}).reset_index()
    attendance_df = attendance_df.rename(columns={"StudentName_SID": "Number of Attendees"})
    attendance_df["Date"] = attendance_df["AttendedDate"]
    attendance_df = attendance_df[["name_professor_section", "Date", "Number of Attendees"]]

    # Create pie chart for total number of classes
    class_totals_fig = go.Figure(data=[go.Pie(labels=class_totals_df["name_professor_section"], values=class_totals_df["Total Number of Classes"])])
    class_totals_fig.update_layout(title="Total Number of Classes")

    # Create bar graph for total number of students in the class
    courses_fig = go.Figure(data=[go.Bar(x=courses_df["name_professor_section"], y=courses_df["Total Number of Students"])])
    courses_fig.update_layout(title="Total Number of Students in the Class")

    # Create pie chart for total attendees from the latest class
    attendance_fig = go.Figure(data=[go.Pie(labels=["Total Attendees", "Abscentees"], values=[courses_df["Total Attendees"].sum(), courses_df["Total Number of Students"].sum() - courses_df["Total Attendees"].sum() ])])
    # attendance_fig.update_traces(hoverinfo='label+percent', textinfo='value', textfont_size=20,
    #                 marker=dict(colors=['#1f77b4', '#ff7f0e'], line=dict(color='#000000', width=2)))
    attendance_fig.update_layout(title="Total Attendees from the Latest Class")
    attendance_by_date = attendance_collection.aggregate([
    {
        "$match":
        {
            "name_professor_section": name_professor_section
        }
    },
    {
        "$group": {
            "_id": "$AttendedDate",
            "Total Attendees": {"$sum": {"$cond": [{"$eq": ["$Status", "Present"]}, 1, 0]}}
        }
    },
    {
        "$sort": {"_id": 1}
    }
    ])

    # Convert the aggregation result to a DataFrame
    attendance_df = pd.DataFrame(list(attendance_by_date))

    # Rename the "_id" column to "Date"
    attendance_df = attendance_df.rename(columns={"_id": "Date"})

    # Convert the "Date" column to a datetime type
    attendance_df["Date"] = pd.to_datetime(attendance_df["Date"])

    # attendance_by_date_fig = go.Figure(data=go.Scatter(x=attendance_df["Date"], y=attendance_df["Total Attendees"], mode="markers"))
    attendance_by_date_fig = go.Figure(data=go.Bar(x=attendance_df["Date"], y=attendance_df["Total Attendees"]))

# Update the layout
    attendance_by_date_fig.update_layout(title="Number of Students Present by Date", xaxis_title="Date", yaxis_title="Total Attendees", xaxis=dict(tickformat="%Y-%m-%d"))

    # Combine all graphs into one page

    # fig = make_subplots(rows=2, cols=2, specs=[[{'type':'pie'}, {'type':'bar'}], [{'type':'pie'}, {'type':'scatter'}]], subplot_titles=("Total Number of Classes", " Number of Students in the Class", "Total Attendees from the Latest Class", "Number of Attendees by Date"))
    # fig.add_trace(class_totals_fig.data[0], row=1, col=1)
    # fig.add_trace(courses_fig.data[0], row=1, col=2)
    # fig.add_trace(attendance_fig.data[0], row=2, col=1)
    # for trace in attendance_by_date_fig.data:
    #     fig.add_trace(trace, row=2, col=2)
    # fig.update_layout(height=800, width=1000, title=name_professor_section + " Statistics")
    # fig.show()

    # class_totals_html = plotly.io.to_html(class_totals_fig, include_plotlyjs=False, full_html=False)
    # courses_html = plotly.io.to_html(courses_fig, include_plotlyjs=False, full_html=False)
    attendance_html = plotly.io.to_html(attendance_fig, include_plotlyjs=False, full_html=False)
    attendance_by_date_html = plotly.io.to_html(attendance_by_date_fig, include_plotlyjs=False, full_html=False)
    # print(class_totals)
    
    # class_totals_fig_json = json.dumps(class_totals_fig, cls=plotly.utils.PlotlyJSONEncoder)
    # courses_fig_json = json.dumps(courses_fig, cls=plotly.utils.PlotlyJSONEncoder)
    # attendance_fig_json = json.dumps(attendance_fig, cls=plotly.utils.PlotlyJSONEncoder)
    # attendance_by_date_fig_json = json.dumps(attendance_by_date_fig, cls=plotly.utils.PlotlyJSONEncoder)

    attendance_data_list = list(attendance_collection.find({"name_professor_section": name_professor_section}).sort("AttendedDate", pymongo.ASCENDING))
    # print("attendence---",attendance_data_list)

    return render_template('get_stats.html', 
                           username=current_user.id, 
                           course=name_professor_section,
                           total_students=total_number_of_students,
                           attendance_df=attendance_data_list,
                           attendance_html=attendance_html, 
                           attendance_by_date_html=attendance_by_date_html)
    # attendance_course_mapping = {}
    # for course in courses:
    #     attendance = db.attendance.find({"course_name": course})
    #     # persons_with_attendance.append({"course": course, "attendande": attendande})
    #     persons_with_attendance = []
    #     for row in attendance:
    #         display_name = '_'.join(row["student"].split('_')[:2])
    #         persons_with_attendance.append({'name': row["student"], 'display_name': display_name, 'image': course+"/"+row["student"]+".png", "attendance_status": row["attendance_status"]})
    #     if len(persons_with_attendance) > 0:
    #         attendance_course_mapping[course] = persons_with_attendance
    
    # return render_template('view_attendance.html', attendance_course_mapping=attendance_course_mapping, username = current_user.id, courses=courses)

@app.route('/about')
@login_required
def about():
    return render_template('about.html', username = current_user.id)

@app.route('/contact')
@login_required
def contact():
    return render_template('contacts.html', username = current_user.id)

@app.route("/view_attendance_date", methods=["GET", "POST"])
@login_required
def view_attendance_date():
    username = current_user.id
    selected_course = request.form['selected_course_date']
    attendace_date = request.form['attendace_date']
    attendance_course_mapping = {}
    attendance_list = attendance_collection.find({"name_professor_section": selected_course, "AttendedDate": attendace_date})
    persons_with_attendance = []
    for row in attendance_list:
        display_name = row["StudentName_SID"]
        name = row["StudentName_SID"]+"_001"
        persons_with_attendance.append({'name': name, 'display_name': display_name, 'image': selected_course+"/"+name+".png", "attendance_status": True if row["Status"] == 'Present' else False})
    print(persons_with_attendance)
    return render_template('view_attendance.html', persons_with_attendance=persons_with_attendance, username = current_user.id, course=selected_course, date=attendace_date)



def get_courses():
    directory_path = app.config['UPLOAD_FOLDER']+"/"+current_user.id.split("@")[0]

    if not os.path.exists(directory_path):
        return []

    if not os.path.exists(directory_path):
        shutil.copytree(directory_path, "static/"+current_user.id.split("@")[0]+"/")

    # Get a list of all folders in the directory
    folders = os.listdir(directory_path)
    # Create an empty list to store the cards
    cards = []
    # Loop through each folder in the directory
    for folder in folders:
        # Set the folder path
        folder_path = os.path.join(directory_path, folder)
        # Get a list of all images in the folder
        images = os.listdir(folder_path)
        # Create a dictionary to store the folder name and images
        folder_data = {
            "display_name": folder,
            "name": current_user.id.split("@")[0]+"/"+folder,
            "images": images,
            "student": [i.split(".")[0] for i in images ],
        }
        attendace = db.attendance.find({"course_name": folder})
        for a in attendace:
            print(a['student']+"--"+('present' if a['attendance_status'] else 'Abscent'))
        # Add the folder data to the cards list
        cards.append(folder_data)
        print(cards)
    return cards

if __name__ == '__main__':
    app.run(host="0.0.0.0", port="8082", debug=True)

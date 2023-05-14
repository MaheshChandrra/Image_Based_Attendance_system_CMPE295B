from pymongo import MongoClient, IndexModel
from bson import ObjectId
from werkzeug.security import generate_password_hash
from urllib.parse import quote_plus
from datetime import datetime
# Escape the username and password, and create the connection string
username = ""
password = ""
cluster_address = ""
db_name = "attendance_system_db"

# uri = f"mongodb+srv://{quote_plus(username)}:{quote_plus(password)}@{cluster_address}/{db_name}?retryWrites=true&w=majority&ssl=true&ssl_cert_reqs=CERT_NONE"
uri = "mongodb://localhost:27017"
client = MongoClient(uri)
db = client[db_name]

course_schema = {
    "name_professor_section": str,
    "students": {"$set": str}  # Define a set of strings for interests
}
courses_collection = db["courses"]
courses_collection.create_index("name_professor_section", unique=True)

# Create the "attendance" collection
attendance_collection = db["attendance"]

# Define the schema for the "attendance" collection
attendance_schema = {
    "name_professor_section": str,
    "StudentName_SID": str,
    "AttendedDate": str,
    "Status": str
}

# Create the indexes for the "attendance" collection
attendance_indexes = [
    IndexModel(
        [
            ("name_professor_section", 1),
            ("StudentName_SID", 1),
            ("AttendedDate", 1),
            ("Status", 1),
        ],
        name="attendance_index",
    )
]

# Create the indexes for the "attendance" collection
attendance_collection.create_indexes(attendance_indexes)

# Create the "class_totals" collection
class_totals_collection = db["class_totals"]

# Define the schema for the "class_totals" collection
class_totals_schema = {
    "name_professor_section": str,
    "classes_number": {"$numberInt":"0"},
    "previous_dates": {"$set": str}
}

# Create the indexes for the "class_totals" collection
class_totals_indexes = [
    IndexModel([("name_professor_section", 1)], name="class_totals_index")
]

# Create the indexes for the "class_totals" collection
class_totals_collection.create_indexes(class_totals_indexes)
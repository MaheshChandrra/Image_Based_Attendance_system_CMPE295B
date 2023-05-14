import cv2
import facial_recognition
import pickle
import os
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from firebase_admin import  storage
import config
import face_recognition
from flask_login import current_user


# cred = credentials.Certificate("cmpe-295b-frs-195185baef71.json")
# firebase_admin.initialize_app(cred, {
#     'databaseURL': "Students",
#     'storageBucket': "cmpe-295b-frs.appspot.com"
# })


# Importing student images

def generate_face_encodings(class_name,class_path,user_name):
    print("The classpath is ",class_path)
    folderPath = class_path+"/"+class_name
    pathList = os.listdir(folderPath)
    print(pathList)


    imgList = []
    studentIds = []
    for path in pathList:
        imgList.append(cv2.imread(os.path.join(folderPath, path)))
        studentIds.append(os.path.splitext(path)[0])
    print(studentIds)

    start_encoding(imgList,studentIds,class_name,user_name)
    


def findEncodings(imagesList):
    encodeList = []
    for img in imagesList:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encode = face_recognition.face_encodings(img)[0]
        encodeList.append(encode)
        print(encode)
        print("#"*10)
    return encodeList

def start_encoding(imgList,studentIds,class_name,user_name):

    print("[INFO] Encoding Started for class:",class_name)

    print(imgList)
    encodeListKnown = findEncodings(imgList)
    encodeListKnownWithIds = [encodeListKnown, studentIds]
    print("[INFO] Encoding Started for class:",class_name)
    USER_NAME=current_user.id.split("@")[0]


    EMBEDDINGS_PATH=config.FACE_EMBEDDINGS_PATH+'/'+user_name

    file = open(EMBEDDINGS_PATH+"-"+class_name+".p", 'wb')
    pickle.dump(encodeListKnownWithIds, file)
    file.close()
    print("[INFO] Encodings saved for class",class_name)



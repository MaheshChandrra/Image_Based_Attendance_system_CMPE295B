import os
import pickle
import numpy as np
import cv2
import face_recognition
import cvzone
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from firebase_admin import storage
import numpy as np
from datetime import datetime
import config
import pickle
import config
import matplotlib.pyplot as plt
from PIL import Image



def get_faces_from_group_pic(class_name,target_image_name):
    # Load the input image
    # image = cv2.imread(config.GROUP_PICTURE_PATH+class_name+"/"+target_image_name)
    image = cv2.imread(target_image_name)

    # # Convert the input image from BGR to RGB color space
    # rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # Detect all the faces in the image
    face_locations = face_recognition.face_locations(image)

    ## Images from the group pic
    images_from_gp=[]

    # Loop over the face locations
    for face_location in face_locations:
        # Extract the coordinates of the face location
        top, right, bottom, left = face_location

        # Crop the face from the input image
        face_image = image[top:bottom, left:right]

        # Display the extracted face image
        # cv2.imshow("Face", face_image)
        # plt.show()
        # plt.imshow(face_image)
        # plt.show()
        # cv2.waitKey(0)
        images_from_gp.append(face_image)
    return images_from_gp


def compare_faces(class_name,images_from_gp,USER_NAME):
    print("[INFO] Loading Encode File ...")
    EMBEDDINGS_PATH=config.FACE_EMBEDDINGS_PATH+"/"+USER_NAME+"-"+class_name+".p"
    file = open(EMBEDDINGS_PATH, 'rb')
    encodeListKnownWithIds = pickle.load(file)
    file.close()
    encodeListKnown, studentIds = encodeListKnownWithIds
    # print(studentIds)
    print("[INFO] Encode File Loaded")

    modeType = 0
    counter = 0
    id = -1
    imgStudent = []
    image_index=0

    predicted_persons=[]

    while image_index<len(images_from_gp):
        
        # success, img = cap.read()
        img=images_from_gp[image_index]
        imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
        imgS = cv2.cvtColor(images_from_gp[image_index], cv2.COLOR_BGR2RGB)

        faceCurFrame = face_recognition.face_locations(imgS)
        encodeCurFrame = face_recognition.face_encodings(imgS, faceCurFrame)
        # plt.imshow(imgS)
        # plt.show()

        if faceCurFrame:
            person={}
            for encodeFace, faceLoc in zip(encodeCurFrame, faceCurFrame):
                matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
                faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)
                print("matches", matches)
                print("faceDis", faceDis)

                matchIndex = np.argmin(faceDis)
                print("Match Index", matchIndex)

                if matches[matchIndex]:
                    print("Known Face Detected")
                    print(studentIds[matchIndex])

                    img_path="static/images/results/"+class_name
                    isExist = os.path.exists(img_path)
                    if not isExist:
                        # Create a new directory because it does not exist
                        os.makedirs(img_path)

                    
                    person['name']=studentIds[matchIndex]
                    person['image']=img_path+"/"+studentIds[matchIndex]+".jpeg"


                    Image.fromarray(imgS).save(person['image'])
                   # result=cv2.imwrite(person['image'], imgS)

                    person['image']='/'.join(person['image'].split("/")[2:])
                    
                    predicted_persons.append(person)
                    id = studentIds[matchIndex]

        else:
            print("[ERROR] No Face Detected")
            if not isExist:
                #Create a new directory because it does not exist
                os.makedirs(img_path)  
            
            person['name']="not_detected_"+str(image_index)
            person['image']=img_path+"/"+studentIds[matchIndex]+".jpeg"


            # result=cv2.imwrite(person['image'], imgS)
            Image.fromarray(imgS).save(person['image'])
            person['image']='/'.join(person['image'].split("/")[2:])
            predicted_persons.append(person)
        print(person)

        image_index+=1
    print("[INFO] Facial Recognition Process Completed")
    return predicted_persons


def perform_face_recognition(class_name,target_image_name,USER_NAME):

    print(target_image_name)
    
    ### Separate faces from group picture
    list_of_individual_faces=get_faces_from_group_pic(class_name,target_image_name)

    ### Perform Distance comparision on images
    predicted_persons_result=compare_faces(class_name,list_of_individual_faces,USER_NAME)

    print(predicted_persons_result)

    return predicted_persons_result

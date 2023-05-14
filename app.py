import face_encoder
import facial_recognition

test_class_name="class_1"
group_picture="team_img_7.jpeg"

face_encoder.generate_face_encodings(test_class_name)
facial_recognition.perform_face_recognition(test_class_name,group_picture)


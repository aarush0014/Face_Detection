import os
import dlib
import csv
import numpy as np
import logging
import cv2
import sqlite3

# Path of cropped faces
path_images_from_camera = "data/data_faces_from_camera/"
csv_file_path = "data/features_all.csv"
db_file_path = "attendance.db"

# Use frontal face detector of Dlib
detector = dlib.get_frontal_face_detector()
# Get face landmarks
predictor = dlib.shape_predictor('data/data_dlib/shape_predictor_68_face_landmarks.dat')
# Use Dlib resnet50 model to get 128D face descriptor
face_reco_model = dlib.face_recognition_model_v1("data/data_dlib/dlib_face_recognition_resnet_model_v1.dat")

# Return 128D features for a single image
def return_128d_features(path_img):
    img_rd = cv2.imread(path_img)
    faces = detector(img_rd, 1)

    logging.info("%-40s %-20s", " Image with faces detected:", path_img)

    if len(faces) != 0:
        shape = predictor(img_rd, faces[0])
        face_descriptor = face_reco_model.compute_face_descriptor(img_rd, shape)
    else:
        face_descriptor = 0
        logging.warning("no face")
    return face_descriptor

# Return the mean value of 128D face descriptor for person X
def return_features_mean_personX(path_face_personX):
    features_list_personX = []
    photos_list = os.listdir(path_face_personX)
    if photos_list:
        for i in range(len(photos_list)):
            logging.info("%-40s %-20s", " / Reading image:", path_face_personX + "/" + photos_list[i])
            features_128d = return_128d_features(path_face_personX + "/" + photos_list[i])
            if features_128d == 0:
                continue  # Skip if no face detected
            features_list_personX.append(features_128d)
    else:
        logging.warning(" Warning: No images in %s/", path_face_personX)

    if features_list_personX:
        features_mean_personX = np.array(features_list_personX, dtype=object).mean(axis=0)
    else:
        features_mean_personX = np.zeros(128, dtype=object, order='C')
    return features_mean_personX

# Function to insert data into SQLite database
def insert_data_into_db():
    # Connect to SQLite database (it will create the database if it doesn't exist)
    conn = sqlite3.connect(db_file_path)
    cursor = conn.cursor()

    cursor.execute('''
        DROP TABLE IF EXISTS data
    ''')

    # Create a table for data if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS data (
        name TEXT NOT NULL,
        roll_no INTEGER NOT NULL
    )
    ''')

    # Read the features from the CSV and insert into the database
    with open(csv_file_path, "r") as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            # Assuming the first two elements are name and roll_no
            person_name = row[0]
            roll_no = int(row[1]) if row[1].isdigit() else None
            cursor.execute('''
            INSERT INTO data (name, roll_no) VALUES (?, ?)
            ''', (person_name, roll_no))

    # Commit the changes and close the connection
    conn.commit()
    conn.close()

def main():
    logging.basicConfig(level=logging.INFO)
    person_list = os.listdir(path_images_from_camera)
    person_list.sort()

    with open(csv_file_path, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        for person in person_list:
            logging.info("%sperson_%s", path_images_from_camera, person)
            features_mean_personX = return_features_mean_personX(path_images_from_camera + person)

            # Extract name and roll number
            if len(person.split('_', 2)) == 2:
                person_name = person
                person_rno = None
            elif len(person.split('_', 3)) == 3:
                person_name = person.split('_', 3)[-1]
                person_rno = None
            else:
                person_name = person.split('_', 3)[-2]
                person_rno = person.split('_', 3)[-1]

            ins = [person_name, person_rno]  # Changed rollno to roll_no
            features_mean_personX = np.insert(features_mean_personX, 0, ins, axis=0)
            writer.writerow(features_mean_personX)
            logging.info('\n')

    logging.info("Save all the features of faces registered into: %s", csv_file_path)

    # Insert the data into the SQLite database
    insert_data_into_db()

if __name__ == '__main__':
    main()

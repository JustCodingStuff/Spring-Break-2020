import numpy as np
import cv2
import face_recognition
import os

# Absolute directory to the folder containing all of the sub-folders each titled with the individual's name and
# filled with images of only the individual
DIRECTORY = "Absolute\\path\\to\\folder\\with\\faces"

MODEL = "hog"
TOLERANCE = 0.55
known_faces = {}
known_face_encodings = {}

# Uses the computer's default camera for the video capture
cap = cv2.VideoCapture(0)

# Opens folder containing all of the sub-folders and loops through each sub-folder,
# Where each sub-folder contains a set of photos for a single individual
for face_folder in os.listdir(DIRECTORY):
    name = os.path.splitext(face_folder)[0]
    individuals_faces = []

    # Loops through the images in each sub-folder and creates a dictionary entry with the sub-folder's/person's name
    # and the image files
    for face_file in os.listdir(f"{DIRECTORY}\\{face_folder}"):
        individuals_faces.append(face_recognition.load_image_file(f"{DIRECTORY}\\{face_folder}\\{face_file}"))
    known_faces.update({name: individuals_faces})

# Loops through the names of the people in the sub-folder
for known_face_name in known_faces.keys():
    name = known_face_name
    individuals_encodings = []

    # Loops through the image files under the person's name and encodes the faces found in each image
    for image_file in known_faces[name]:
        individuals_encodings.append(face_recognition.face_encodings(image_file)[0])
    known_face_encodings.update({name: individuals_encodings})

# Runs indefinitely
while True:
    ret, frame = cap.read()

    # Makes a smaller frame to increase processing speeds
    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

    # Converts/Reverses the BGR value that cv2 uses so that it is RGB
    rgb_small_frame = small_frame[:, :, ::-1]

    # Finds all of the faces and face locations in the frame and encodes them
    face_locations = face_recognition.face_locations(rgb_small_frame, model=MODEL)
    face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

    face_names = []

    # Loops through the face encodings of the faces found in the frame
    for face_encoding in face_encodings:
        identity = "Unknown"
        lowest_best_match = 1000

        # Loops through the names in the known encodings dictionary
        for name in known_face_encodings:

            # Gets all of the known encodings for the person given their name
            known_encodings = known_face_encodings[name]

            # Compares the face encoding from the frame (the unknown person) with the known encodings of the
            # individual with the given name and stores a boolean value for each comparison in a list
            matches = face_recognition.compare_faces(known_encodings, face_encoding, tolerance=TOLERANCE)

            # If there is a True (a match) in matches found after the comparison the smallest distance between face
            # encoding of the person in the frame and the known encodings will be found
            if True in matches:
                face_distances = face_recognition.face_distance(known_encodings, face_encoding)
                best_match = np.amin(face_distances)
                best_match_index = np.argmin(face_distances)

                # Checks to see if the smallest difference in face encodings was a match and is lower than the
                # current lowest distance, which ensures the closest match is found
                if matches[best_match_index] and best_match < lowest_best_match:
                    lowest_best_match = best_match
                    identity = name

        # Adds the name of the person to a list
        face_names.append(identity)

    for (top, right, bottom, left), name in zip(face_locations, face_names):
        # Scale back up face locations since the frame we detected in was scaled to 1/4 size
        top *= 4
        right *= 4
        bottom *= 4
        left *= 4

        # Draw a box around the face
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

        # Draw a label with the given person's name below the face
        cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
        font = cv2.FONT_HERSHEY_DUPLEX
        cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)

    # Display the resulting image
    cv2.imshow('Video', frame)

    # Stop the program if the q key is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
cap.release()
cv2.destroyAllWindows()

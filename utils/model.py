import json
import tensorflow as tf
import numpy as np
import cv2
import time

# Loading Model and Label
IMG_SIZE = 224

with open("labels.json", "r") as f:
    meta = json.load(f)

LABELS = meta["classes"]

model = tf.keras.models.load_model("vgg_FT_best.keras")

# Haar Cascade
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

# Prediction Function
def predict_rgb_face(face_rgb):
    face_rgb_resized = cv2.resize(face_rgb, (IMG_SIZE, IMG_SIZE))
    face_rgb_resized = np.expand_dims(face_rgb_resized, axis=0)
    face_rgb_resized = tf.keras.applications.vgg16.preprocess_input(face_rgb_resized)

    probs = model.predict(face_rgb_resized, verbose=0)[0]
    idx = int(np.argmax(probs))

    return LABELS[idx], float(probs[idx])

# Face Detection
def detect_face_and_predict(frame_bgr):
    gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    detected_name = None

    for (x, y, w, h) in faces:
        face_bgr = frame_bgr[y:y+h, x:x+w]
        face_rgb = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2RGB)

        name, conf = predict_rgb_face(face_rgb)
        detected_name = name

        # Draw Box + Label
        cv2.rectangle(frame_bgr, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.putText(frame_bgr, f"{name} ({conf:.2f})",
                    (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX,
                    0.7, (0, 255, 0), 2)

    return detected_name, frame_bgr

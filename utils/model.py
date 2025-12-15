import json
import os
import tensorflow as tf
import numpy as np
import cv2
import streamlit as st
import gdown

# ---------------------------
# CONFIG
# ---------------------------
IMG_SIZE = 224
MODEL_PATH = "vgg_FT_best.keras"
LABELS_PATH = "labels.json"

# Disable GPU safely (Streamlit Cloud)
try:
    tf.config.set_visible_devices([], "GPU")
except Exception:
    pass


# ---------------------------
# LOAD MODEL & LABELS (G-DRIVE + CACHED)
# ---------------------------

MODEL_FILE_ID = "1Ad5C1Wc2OsLwWbnSEjH3XW8XLaff7f4o"
MODEL_URL = f"https://drive.google.com/uc?id={MODEL_FILE_ID}"

@st.cache_resource
def load_model_and_labels():
    # Download model if missing
    if not os.path.exists(MODEL_PATH):
        with st.spinner("Downloading AI model (first run only)..."):
            gdown.download(MODEL_URL, MODEL_PATH, quiet=False)

    if not os.path.exists(LABELS_PATH):
        raise FileNotFoundError(f"Labels file not found: {LABELS_PATH}")

    with open(LABELS_PATH, "r") as f:
        labels = json.load(f)["classes"]

    model = tf.keras.models.load_model(MODEL_PATH)

    return model, labels


# 🔑 LOAD ONCE (CACHED)
MODEL, LABELS = load_model_and_labels()


# ---------------------------
# FACE DETECTOR
# ---------------------------
@st.cache_resource
def load_face_cascade():
    cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )
    if cascade.empty():
        raise RuntimeError("Failed to load Haar cascade")
    return cascade


FACE_CASCADE = load_face_cascade()


# ---------------------------
# PREDICTION
# ---------------------------
def predict_rgb_face(face_rgb):
    face_resized = cv2.resize(face_rgb, (IMG_SIZE, IMG_SIZE))
    face_resized = np.expand_dims(face_resized, axis=0)
    face_resized = tf.keras.applications.vgg16.preprocess_input(face_resized)

    probs = MODEL.predict(face_resized, verbose=0)[0]
    idx = int(np.argmax(probs))

    return LABELS[idx], float(probs[idx])


# ---------------------------
# FACE DETECTION + ANNOTATION
# ---------------------------
def detect_face_and_predict(frame_bgr):
    gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
    faces = FACE_CASCADE.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)

    best_name = None
    best_conf = 0.0

    for (x, y, w, h) in faces:
        face_bgr = frame_bgr[y:y + h, x:x + w]
        face_rgb = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2RGB)

        name, conf = predict_rgb_face(face_rgb)

        if conf > best_conf:
            best_conf = conf
            best_name = name

        cv2.rectangle(frame_bgr, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(
            frame_bgr,
            f"{name} ({conf:.2f})",
            (x, y - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2,
        )

    return best_name, frame_bgr


import os
import tempfile
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'

import cv2
import numpy as np
import base64
from tensorflow.keras.models import load_model
from ultralytics import YOLO
from fastapi import UploadFile
from typing import Optional
from app.services.tracker_manager import get_session_manager

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MASK_MODEL_PATH = os.path.join(BASE_DIR, "..", "..", "model", "model.h5")

face_detector = YOLO('yolov8n-face.pt') 

mask_net = load_model(MASK_MODEL_PATH)

def detect_and_predict_mask(image, draw_on_image=True):
    (h, w) = image.shape[:2]
    faces_list = []
    locations = []

    results_yolo = face_detector(image, conf=0.5, verbose=False)

    for r in results_yolo:
        boxes = r.boxes
        for box in boxes:
            b = box.xyxy[0].cpu().numpy().astype(int)
            startX, startY, endX, endY = b

            startX, startY = max(0, startX), max(0, startY)
            endX, endY = min(w - 1, endX), min(h - 1, endY)

            face = image[startY:endY, startX:endX]
            if face.size == 0:
                continue

            face_input = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)
            face_input = cv2.resize(face_input, (128, 128))
            face_input = face_input / 255.0
            face_input = np.expand_dims(face_input, axis=0)

            faces_list.append(face_input)
            locations.append((startX, startY, endX, endY))

    final_results = []

    if len(faces_list) > 0:
        faces_array = np.vstack(faces_list)
        predictions = mask_net.predict(faces_array, batch_size=32, verbose=0)

        for box, pred in zip(locations, predictions):
            (nomask, mask) = pred
            label = "Mask" if mask > nomask else "No Mask"
            confidence = float(max(mask, nomask))

            (startX, startY, endX, endY) = box
            
            if draw_on_image:
                color = (0, 255, 0) if label == "Mask" else (0, 0, 255)
                cv2.rectangle(image, (startX, startY), (endX, endY), color, 3)
                label_text = f"{label}: {confidence:.2f}"
                y = startY - 10 if startY - 10 > 10 else startY + 10
                cv2.putText(image, label_text, (startX, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

            final_results.append({
                "box": {"startX": int(startX), "startY": int(startY), "endX": int(endX), "endY": int(endY)},
                "label": label,
                "confidence": round(confidence, 4)
            })

    response = {
        "faces_detected": len(final_results),
        "results": final_results,
        "width": w,
        "height": h
    }

    if draw_on_image:
        _, buffer = cv2.imencode('.jpg', image)
        image_base64 = base64.b64encode(buffer).decode('utf-8')
        response["image_base64"] = image_base64

    return response

def save_upload_file_tmp(upload_file: UploadFile) -> str:
    suffix = os.path.splitext(upload_file.filename)[1]
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(upload_file.file.read())
    tmp.flush()
    tmp.close()
    return tmp.name

def predict_from_image_path(image_path: str, draw_on_image=True):
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError("Cannot read image")
    return detect_and_predict_mask(image, draw_on_image=draw_on_image)

# Bot-sort tracking
def detect_and_predict_mask_with_tracking(image, session_id: str, draw_on_image=True):
    (h, w) = image.shape[:2]
    
    # Get or create tracking session
    session_manager = get_session_manager()
    tracker_session = session_manager.get_or_create_session(session_id)
    
    faces_list = []
    locations = []
    track_ids = []

    # Use BoT-SORT tracking instead of simple detection
    results_yolo = face_detector.track(
        image, 
        conf=0.5, 
        verbose=False,
        tracker="botsort.yaml",
        persist=True  # Maintain tracker state across calls
    )

    for r in results_yolo:
        boxes = r.boxes
        for box in boxes:
            b = box.xyxy[0].cpu().numpy().astype(int)
            startX, startY, endX, endY = b

            startX, startY = max(0, startX), max(0, startY)
            endX, endY = min(w - 1, endX), min(h - 1, endY)

            face = image[startY:endY, startX:endX]
            if face.size == 0:
                continue

            face_input = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)
            face_input = cv2.resize(face_input, (128, 128))
            face_input = face_input / 255.0
            face_input = np.expand_dims(face_input, axis=0)

            faces_list.append(face_input)
            locations.append((startX, startY, endX, endY))
            
            # Extract track ID from BoT-SORT
            if box.id is not None:
                track_id = int(box.id.cpu().numpy()[0])
                track_ids.append(track_id)
            else:
                track_ids.append(-1)  # No track ID assigned

    final_results = []

    if len(faces_list) > 0:
        faces_array = np.vstack(faces_list)
        predictions = mask_net.predict(faces_array, batch_size=32, verbose=0)

        for box, pred, track_id in zip(locations, predictions, track_ids):
            (nomask, mask) = pred
            raw_label = "Mask" if mask > nomask else "No Mask"
            raw_confidence = float(max(mask, nomask))

            # Update tracking session with raw prediction
            if track_id != -1:
                tracker_session.update_track(track_id, raw_label, raw_confidence)
                # Get smoothed prediction from history
                label, confidence = tracker_session.get_smoothed_prediction(track_id)
            else:
                # No tracking, use raw prediction
                label = raw_label
                confidence = raw_confidence

            (startX, startY, endX, endY) = box
            
            if draw_on_image:
                color = (0, 255, 0) if label == "Mask" else (0, 0, 255)
                cv2.rectangle(image, (startX, startY), (endX, endY), color, 3)
                
                # Include track ID in label for debugging
                if track_id != -1:
                    label_text = f"ID:{track_id} {label}: {confidence:.2f}"
                else:
                    label_text = f"{label}: {confidence:.2f}"
                    
                y = startY - 10 if startY - 10 > 10 else startY + 10
                cv2.putText(image, label_text, (startX, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

            final_results.append({
                "box": {"startX": int(startX), "startY": int(startY), "endX": int(endX), "endY": int(endY)},
                "label": label,
                "confidence": round(confidence, 4),
                "track_id": track_id
            })

    response = {
        "faces_detected": len(final_results),
        "results": final_results,
        "width": w,
        "height": h,
        "session_id": session_id
    }

    if draw_on_image:
        _, buffer = cv2.imencode('.jpg', image)
        image_base64 = base64.b64encode(buffer).decode('utf-8')
        response["image_base64"] = image_base64

    return response

# predict every frame
def predict_from_image_path_with_tracking(image_path: str, session_id: str, draw_on_image=True):
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError("Cannot read image")
    return detect_and_predict_mask_with_tracking(image, session_id, draw_on_image=draw_on_image)

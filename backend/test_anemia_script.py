import os
import django
import sys
import cv2

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nutriscan_project.settings')
django.setup()

from scanner.utils.face_detector import FaceDetector
from scanner.utils.feature_analyzer import FeatureAnalyzer

image_path = "test_face.jpg"

if not os.path.exists(image_path):
    print(f"Error: Need a test face photo saved as {image_path} in the backend folder")
    sys.exit()

face_detector = FaceDetector()
feature_analyzer = FeatureAnalyzer()

print(f"Testing Anemia Extraction on {image_path}...")

face_result = face_detector.detect_faces(image_path)
if not face_result['face_detected']:
    print("No face detected in test image.")
    sys.exit()

landmarks = face_result['landmarks']

# 1. Forehead (Baseline)
forehead_roi = face_detector.extract_roi(image_path, landmarks, 'forehead')
forehead_color = feature_analyzer.analyze_color(forehead_roi) if forehead_roi is not None else None

# 2. Lips
best_lip_color = None
for lip_region in ['upper_lip', 'lower_lip']:
    lip_roi = face_detector.extract_roi(image_path, landmarks, lip_region)
    if lip_roi is not None:
        lip_color = feature_analyzer.analyze_color(lip_roi)
        # Just grab the first valid one for the test
        if lip_color:
            best_lip_color = lip_color
            break

# 3. Under eyes
best_under_eye_color = None
for eye_region in ['left_under_eye', 'right_under_eye']:
    eye_roi = face_detector.extract_roi(image_path, landmarks, eye_region)
    if eye_roi is not None:
        eye_color = feature_analyzer.analyze_color(eye_roi)
        if eye_color:
            if best_under_eye_color is None:
                best_under_eye_color = eye_color
            else:
                if eye_color['lab']['l'] < best_under_eye_color['lab']['l']:
                    best_under_eye_color = eye_color

print("\n--- Extracted Colors ---")
print(f"Forehead: {forehead_color}")
print(f"Lips: {best_lip_color}")
print(f"Under-Eye: {best_under_eye_color}")

print("\n--- Running check_anemia ---")
score = feature_analyzer.check_anemia(
    lip_color=best_lip_color,
    under_eye_color=best_under_eye_color,
    baseline_color=forehead_color
)

print(f"\nFINAL ANEMIA VISUAL SCORE: {score}/10")

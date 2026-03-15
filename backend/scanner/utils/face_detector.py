import cv2
import numpy as np
import os
import urllib.request

# ──────────────────────────────────────────────────────────────────────────────
# MediaPipe Tasks API model — downloaded once to the utils/ directory
# ──────────────────────────────────────────────────────────────────────────────
_MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/"
    "face_landmarker/face_landmarker/float16/1/face_landmarker.task"
)
_MODEL_PATH = os.path.join(os.path.dirname(__file__), "face_landmarker.task")


def _ensure_model():
    """Download the FaceLandmarker model file if not already present."""
    if not os.path.exists(_MODEL_PATH):
        print("[NutriScan] Downloading MediaPipe FaceLandmarker model (~3 MB)...")
        urllib.request.urlretrieve(_MODEL_URL, _MODEL_PATH)
        print("[NutriScan] Model downloaded successfully.")


def _load_mediapipe_tasks():
    """
    Load MediaPipe FaceLandmarker via the Tasks API (mediapipe >= 0.10.x).
    Returns a FaceLandmarker instance or None.
    """
    try:
        from mediapipe.tasks import python as mp_tasks
        from mediapipe.tasks.python import vision
        from mediapipe.tasks.python.vision import FaceLandmarkerOptions, RunningMode

        _ensure_model()

        base_options = mp_tasks.BaseOptions(model_asset_path=_MODEL_PATH)
        options = FaceLandmarkerOptions(
            base_options=base_options,
            running_mode=RunningMode.IMAGE,
            num_faces=1,
            min_face_detection_confidence=0.5,
            min_face_presence_confidence=0.5,
            min_tracking_confidence=0.5,
            output_face_blendshapes=False,
            output_facial_transformation_matrixes=False,
        )
        landmarker = vision.FaceLandmarker.create_from_options(options)
        print("[NutriScan] MediaPipe FaceLandmarker (Tasks API) loaded successfully.")
        return ('tasks', landmarker)
    except Exception as e:
        print(f"[NutriScan] Tasks API unavailable: {e}")

    # Fallback: old solutions API (mediapipe < 0.10.x)
    try:
        from mediapipe.python.solutions import face_mesh as mp_fm
        mesh = mp_fm.FaceMesh(
            static_image_mode=True, max_num_faces=1,
            refine_landmarks=True, min_detection_confidence=0.5,
        )
        print("[NutriScan] MediaPipe FaceMesh (solutions API) loaded.")
        return ('solutions', mesh)
    except Exception as e:
        print(f"[NutriScan] solutions API unavailable: {e}")

    return None


class FaceDetector:
    """
    Face detection and landmark extraction.

    Priority order:
      1. MediaPipe FaceLandmarker (Tasks API) — works with mediapipe 0.10.x
      2. MediaPipe FaceMesh (solutions API)   — works with older mediapipe
      3. OpenCV Haar Cascade                  — always available, no download
    """

    def __init__(self):
        result = _load_mediapipe_tasks()
        if result:
            self._mode, self._detector = result
        else:
            self._mode = 'opencv'
            self._detector = None
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            self._face_cascade = cv2.CascadeClassifier(cascade_path)
            print("[NutriScan] Using OpenCV Haar Cascade fallback.")

    # ── Public API ────────────────────────────────────────────────────────────

    def detect_face(self, image_path):
        """
        Detect face and return landmarks.

        Returns:
            dict: { face_detected, landmarks, image_shape, message }
            landmarks is a list of (x, y, z) pixel tuples (MediaPipe modes)
            or a dict {'bbox': (x,y,w,h)} (OpenCV mode).
        """
        image = cv2.imread(image_path)
        if image is None:
            return {'face_detected': False, 'landmarks': None,
                    'image_shape': None, 'message': 'Could not read image'}

        # Brightness check
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        mean_brightness = np.mean(gray)
        if mean_brightness < 40:
            return {'face_detected': False, 'landmarks': None,
                    'image_shape': image.shape, 
                    'message': 'Image is too dark. Please move to a well-lit area.'}

        if self._mode == 'tasks':
            return self._detect_tasks(image)
        elif self._mode == 'solutions':
            return self._detect_solutions(image)
        else:
            return self._detect_opencv(image)

    def get_roi_landmarks(self):
        """MediaPipe landmark indices (same for both Tasks and solutions APIs)."""
        return {
            'left_eye':    [33, 133, 160, 159, 158, 157, 173, 144, 145, 153, 154, 155],
            'right_eye':   [362, 263, 387, 386, 385, 384, 398, 373, 374, 380, 381, 382],
            'left_under_eye': [114, 188, 121, 120, 119, 118, 117, 111, 110, 239],
            'right_under_eye': [343, 412, 350, 349, 348, 347, 346, 340, 339, 459],
            'upper_lip':   [61, 185, 40, 39, 37, 0, 267, 269, 270, 409, 291],
            'lower_lip':   [146, 91, 181, 84, 17, 314, 405, 321, 375, 291],
            'left_cheek':  [123, 116, 117, 118, 50, 101, 36, 205, 206],
            'right_cheek': [352, 345, 346, 347, 280, 330, 266, 425, 426],
            'forehead':    [10, 338, 297, 332, 284, 251, 389, 356, 454],
        }

    def extract_roi(self, image_path, landmarks, roi_name):
        """Extract a facial region of interest from the image."""
        image = cv2.imread(image_path)
        if image is None:
            return None
        try:
            if isinstance(landmarks, dict) and 'bbox' in landmarks:
                return self._extract_roi_from_bbox(image, landmarks['bbox'], roi_name)
            else:
                return self._extract_roi_from_landmarks(image, landmarks, roi_name)
        except Exception as e:
            print(f"[NutriScan] Error extracting ROI '{roi_name}': {e}")
            return None

    # ── MediaPipe Tasks API ───────────────────────────────────────────────────

    def _detect_tasks(self, image):
        try:
            from mediapipe import Image as MpImage, ImageFormat
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            mp_image = MpImage(image_format=ImageFormat.SRGB, data=image_rgb)
            result = self._detector.detect(mp_image)

            if not result.face_landmarks:
                return {'face_detected': False, 'landmarks': None,
                        'image_shape': image.shape,
                        'message': 'No face detected (MediaPipe FaceLandmarker)'}

            h, w = image.shape[:2]
            landmarks = [
                (int(lm.x * w), int(lm.y * h), lm.z)
                for lm in result.face_landmarks[0]
            ]
            
            xs = [pt[0] for pt in landmarks]
            ys = [pt[1] for pt in landmarks]
            face_w = max(xs) - min(xs)
            face_h = max(ys) - min(ys)
            
            if (face_w * face_h) / (w * h) < 0.04:
                return {'face_detected': False, 'landmarks': None,
                        'image_shape': image.shape,
                        'message': 'Face is too distant. Please come closer.'}

            completeness = self._check_face_completeness(landmarks, image.shape)
            if completeness:
                return {'face_detected': False, 'landmarks': None,
                        'image_shape': image.shape,
                        'message': completeness}

            return {'face_detected': True, 'landmarks': landmarks,
                    'image_shape': image.shape,
                    'message': f'Face detected — MediaPipe FaceLandmarker ({len(landmarks)} landmarks)'}
        except Exception as e:
            # Downgrade to OpenCV on unexpected runtime error
            print(f"[NutriScan] Tasks API runtime error: {e} — falling back to OpenCV")
            return self._detect_opencv(image)

    # ── MediaPipe solutions API (legacy) ─────────────────────────────────────

    def _detect_solutions(self, image):
        try:
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = self._detector.process(image_rgb)
            if not results.multi_face_landmarks:
                return {'face_detected': False, 'landmarks': None,
                        'image_shape': image.shape,
                        'message': 'No face detected (MediaPipe FaceMesh)'}
            h, w = image.shape[:2]
            landmarks = [
                (int(lm.x * w), int(lm.y * h), lm.z)
                for lm in results.multi_face_landmarks[0].landmark
            ]
            
            xs = [pt[0] for pt in landmarks]
            ys = [pt[1] for pt in landmarks]
            face_w = max(xs) - min(xs)
            face_h = max(ys) - min(ys)
            
            if (face_w * face_h) / (w * h) < 0.04:
                return {'face_detected': False, 'landmarks': None,
                        'image_shape': image.shape,
                        'message': 'Face is too distant. Please come closer.'}

            completeness = self._check_face_completeness(landmarks, image.shape)
            if completeness:
                return {'face_detected': False, 'landmarks': None,
                        'image_shape': image.shape,
                        'message': completeness}

            return {'face_detected': True, 'landmarks': landmarks,
                    'image_shape': image.shape,
                    'message': f'Face detected — MediaPipe FaceMesh ({len(landmarks)} landmarks)'}
        except Exception as e:
            print(f"[NutriScan] FaceMesh runtime error: {e} — falling back to OpenCV")
            return self._detect_opencv(image)

    # ── OpenCV Haar Cascade (fallback) ────────────────────────────────────────

    def _detect_opencv(self, image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = self._face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(80, 80)
        )
        if len(faces) == 0:
            return {'face_detected': False, 'landmarks': None,
                    'image_shape': image.shape,
                    'message': 'No face detected (OpenCV Haar Cascade)'}
        x, y, fw, fh = faces[0]
        h, w = image.shape[:2]
        
        if (fw * fh) / (w * h) < 0.04:
            return {'face_detected': False, 'landmarks': None,
                    'image_shape': image.shape,
                    'message': 'Face is too distant. Please come closer.'}

        return {'face_detected': True, 'landmarks': {'bbox': (x, y, fw, fh)},
                'image_shape': image.shape,
                'message': 'Face detected — OpenCV Haar Cascade (proportional ROIs)'}

    # ── Face Completeness Check ───────────────────────────────────────────────

    def _check_face_completeness(self, landmarks, image_shape):
        """
        Checks whether the key face zones are visible in the image.

        Required zones:
          - Forehead   : landmark 10
          - Lower lip  : landmark 17  (allows forehead-to-under-lips crop)
          - Left temple: landmark 127
          - Right temple: landmark 356

        Returns an error message string if incomplete, or None if OK.
        """
        ih, iw = image_shape[:2]
        margin = 5  # pixels from edge that counts as "out of frame"

        # Key landmark indices
        KEY_FOREHEAD     = 10
        KEY_LOWER_LIP    = 17
        KEY_LEFT_TEMPLE  = 127
        KEY_RIGHT_TEMPLE = 356

        if len(landmarks) <= max(KEY_FOREHEAD, KEY_LOWER_LIP, KEY_LEFT_TEMPLE, KEY_RIGHT_TEMPLE):
            return None  # Not enough landmarks — skip check

        def in_frame(idx, axis):
            """Check if landmark[idx] is within image bounds on the given axis."""
            coord = landmarks[idx][axis]  # 0=x, 1=y
            limit = iw if axis == 0 else ih
            return margin < coord < (limit - margin)

        forehead_ok      = in_frame(KEY_FOREHEAD,     1)  # y axis
        lower_lip_ok     = in_frame(KEY_LOWER_LIP,    1)  # y axis
        left_temple_ok   = in_frame(KEY_LEFT_TEMPLE,  0)  # x axis
        right_temple_ok  = in_frame(KEY_RIGHT_TEMPLE, 0)  # x axis

        if not forehead_ok:
            return 'Partial face detected: forehead is cut off. Please move down a bit.'
        if not lower_lip_ok:
            return 'Partial face detected: chin/lips are cut off. Please show your full face.'
        if not left_temple_ok or not right_temple_ok:
            return 'Partial face detected: face is cut off on the side. Please center your face.'

        return None  # All good

    # ── ROI Extraction ────────────────────────────────────────────────────────

    def _extract_roi_from_landmarks(self, image, landmarks, roi_name):
        """Precise extraction using MediaPipe landmark coordinates."""
        roi_indices = self.get_roi_landmarks().get(roi_name, [])
        valid = [i for i in roi_indices if i < len(landmarks)]
        if not valid:
            return None
        pts = np.array([(landmarks[i][0], landmarks[i][1]) for i in valid])
        x, y, w, h = cv2.boundingRect(pts)
        pad = 10
        ih, iw = image.shape[:2]
        x1, y1 = max(0, x - pad), max(0, y - pad)
        x2, y2 = min(iw, x + w + pad), min(ih, y + h + pad)
        roi = image[y1:y2, x1:x2]
        return roi if roi.size > 0 else None

    def _extract_roi_from_bbox(self, image, bbox, roi_name):
        """Proportional estimation from bounding box (OpenCV fallback only)."""
        x, y, w, h = bbox
        ih, iw = image.shape[:2]
        regions = {
            'left_eye':    (0.05, 0.15, 0.45, 0.38),
            'right_eye':   (0.55, 0.15, 0.95, 0.38),
            'upper_lip':   (0.25, 0.62, 0.75, 0.75),
            'lower_lip':   (0.25, 0.72, 0.75, 0.85),
            'left_cheek':  (0.02, 0.42, 0.38, 0.65),
            'right_cheek': (0.62, 0.42, 0.98, 0.65),
            'forehead':    (0.20, 0.04, 0.80, 0.20),
        }
        if roi_name not in regions:
            return None
        rx1, ry1, rx2, ry2 = regions[roi_name]
        ax1 = int(max(0, x + rx1 * w))
        ay1 = int(max(0, y + ry1 * h))
        ax2 = int(min(iw, x + rx2 * w))
        ay2 = int(min(ih, y + ry2 * h))
        roi = image[ay1:ay2, ax1:ax2]
        return roi if roi.size > 0 else None

    def __del__(self):
        try:
            if self._mode == 'solutions' and self._detector:
                self._detector.close()
            elif self._mode == 'tasks' and self._detector:
                self._detector.close()
        except Exception:
            pass
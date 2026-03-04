import cv2
import numpy as np


class FeatureAnalyzer:
    """
    Analyze facial features for health indicators:
    - Anemia (Pallor)
    - Jaundice (Yellowness)
    - Dehydration (Dryness)
    - Vitamin Deficiency
    """

    # ==========================================
    # COLOR ANALYSIS (Lighting Normalized)
    # ==========================================
    def analyze_color(self, roi_image):

        if roi_image is None or roi_image.size == 0:
            return None

        try:
            # --- Convert to LAB for lighting normalization ---
            lab = cv2.cvtColor(roi_image, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)

            # Equalize brightness channel
            l = cv2.equalizeHist(l)

            lab = cv2.merge([l, a, b])

            # Convert normalized LAB back to BGR
            normalized_bgr = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

            # Convert normalized image to RGB & HSV
            rgb = cv2.cvtColor(normalized_bgr, cv2.COLOR_BGR2RGB)
            hsv = cv2.cvtColor(normalized_bgr, cv2.COLOR_BGR2HSV)

            mean_rgb = np.mean(rgb, axis=(0, 1))
            mean_hsv = np.mean(hsv, axis=(0, 1))
            mean_lab = np.mean(lab, axis=(0, 1))

            return {
                "rgb": {
                    "red": float(mean_rgb[0]),
                    "green": float(mean_rgb[1]),
                    "blue": float(mean_rgb[2])
                },
                "hsv": {
                    "hue": float(mean_hsv[0]),       # OpenCV range: 0–179
                    "saturation": float(mean_hsv[1]),
                    "value": float(mean_hsv[2])
                },
                "lab": {
                    "l": float(mean_lab[0]),
                    "a": float(mean_lab[1]),
                    "b": float(mean_lab[2])
                }
            }

        except Exception as e:
            print(f"Error analyzing color: {e}")
            return None


    # ==========================================
    # TEXTURE ANALYSIS
    # ==========================================
    def analyze_texture(self, roi_image):

        if roi_image is None or roi_image.size == 0:
            return None

        try:
            gray = cv2.cvtColor(roi_image, cv2.COLOR_BGR2GRAY)

            # Edge density (cracks)
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.sum(edges > 0) / edges.size

            # Roughness (pixel variation)
            roughness = float(np.std(gray))

            # Entropy (texture randomness)
            hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
            hist_norm = hist / (hist.sum() + 1e-6)
            entropy = -np.sum(hist_norm * np.log2(hist_norm + 1e-6))

            return {
                "edge_density": float(edge_density),
                "roughness": roughness,
                "entropy": float(entropy)
            }

        except Exception as e:
            print(f"Error analyzing texture: {e}")
            return None


    # ==========================================
    # ANEMIA (PALLOR)
    # ==========================================
    def check_pallor(self, color_data, baseline_data=None):

        if not color_data:
            return 0

        score = 0
        red = color_data["rgb"]["red"]
        sat = color_data["hsv"]["saturation"]

        if baseline_data:
            base_red = baseline_data["rgb"]["red"]
            base_sat = baseline_data["hsv"]["saturation"]

            red_ratio = red / (base_red + 1e-6)
            sat_ratio = sat / (base_sat + 1e-6)

            if red_ratio < 0.85:
                score += 4
            elif red_ratio < 0.95:
                score += 2

            if sat_ratio < 0.75:
                score += 2

        else:
            if red < 130:
                score += 4
            elif red < 150:
                score += 2

            if sat < 30:
                score += 2

        return min(score, 10)


    # ==========================================
    # JAUNDICE (YELLOWNESS)
    # ==========================================
    def check_yellowness(self, color_data, baseline_data=None):

        if not color_data:
            return 0

        score = 0
        hue = color_data["hsv"]["hue"]
        lab_b = color_data["lab"]["b"]

        # Yellow hue detection (OpenCV range 0–179)
        if 15 <= hue <= 40:
            score += 5

        if baseline_data:
            base_b = baseline_data["lab"]["b"]
            b_ratio = lab_b / (base_b + 1e-6)

            if b_ratio > 1.1:
                score += 3
        else:
            if lab_b > 10:
                score += 3

        return min(score, 10)


    # ==========================================
    # DEHYDRATION (DRYNESS)
    # ==========================================
    def check_dryness(self, texture_data):

        if not texture_data:
            return 0

        score = 0

        if texture_data["edge_density"] > 0.3:
            score += 5
        elif texture_data["edge_density"] > 0.2:
            score += 3

        if texture_data["roughness"] > 40:
            score += 3
        elif texture_data["roughness"] > 30:
            score += 2

        if texture_data["entropy"] > 7.5:
            score += 2

        return min(score, 10)


    # ==========================================
    # VITAMIN DEFICIENCY
    # ==========================================
    def check_vitamin_deficiency(self, color_data, texture_data, baseline_data=None):

        if not color_data or not texture_data:
            return 0

        score = 0

        red = color_data["rgb"]["red"]
        sat = color_data["hsv"]["saturation"]

        # --- Color loss component ---
        if baseline_data:
            base_red = baseline_data["rgb"]["red"]
            red_ratio = red / (base_red + 1e-6)

            if red_ratio < 0.85:
                score += 3
            elif red_ratio < 0.95:
                score += 2
        else:
            if red < 140:
                score += 2

        if sat < 40:
            score += 2

        # --- Texture component ---
        if texture_data["edge_density"] > 0.25:
            score += 2

        if texture_data["roughness"] > 35:
            score += 1

        if texture_data["entropy"] > 7.5:
            score += 2

        return min(score, 10)
import cv2
import numpy as np


class FeatureAnalyzer:
    """
    Analyze facial features for:
    - Jaundice (Yellowness)
    - Vitamin Deficiency (B-complex related signs)
    """

    # ==========================================
    # COLOR ANALYSIS (Lighting Normalized)
    # ==========================================
    def analyze_color(self, roi_image):

        if roi_image is None or roi_image.size == 0:
            return None

        try:
            lab = cv2.cvtColor(roi_image, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)

            # Lighting normalization
            l = cv2.equalizeHist(l)
            lab = cv2.merge([l, a, b])

            normalized_bgr = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

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
                    "hue": float(mean_hsv[0]),
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
            print(f"Color analysis error: {e}")
            return None


    # ==========================================
    # JAUNDICE DETECTION
    # ==========================================
    def check_jaundice(self, sclera_color, skin_color=None):
        """
        Detection based exclusively on eye sclera yellowing.
        Skin tone is NOT used — it varies too much by ethnicity and lighting.
        """

        if not sclera_color:
            return 0

        score = 0

        sclera_hue = sclera_color["hsv"]["hue"]
        sclera_sat = sclera_color["hsv"]["saturation"]
        sclera_b = sclera_color["lab"]["b"]

        # ── HSV Hue: Yellow range 15–40 (camera-normalized) ──────────────────
        # The more centered in the yellow hue range, the more points
        if 15 <= sclera_hue <= 40:
            # Strong center of yellow hue
            if 20 <= sclera_hue <= 35:
                score += 4
            else:
                score += 2

        # ── HSV Saturation: Yellow must be saturated, not just pale ──────────
        # High saturation means vivid yellow, not just off-white
        if sclera_sat > 60:
            score += 2
        elif sclera_sat > 30:
            score += 1

        # ── LAB B channel: positive B = yellow, graduated by intensity ───────
        # LAB B neutrals ~ 128; jaundice pushes it toward 150+
        if sclera_b > 160:      # intense jaundice
            score += 4
        elif sclera_b > 150:    # moderate jaundice
            score += 3
        elif sclera_b > 142:    # mild jaundice
            score += 2
        elif sclera_b > 135:    # very mild / borderline
            score += 1

        return min(score, 10)

    # ==========================================
    # ANEMIA DETECTION
    # ==========================================
    def check_anemia(self, lip_color, under_eye_color, baseline_color=None):
        """
        Detects anemia via:
        - Lip pallor: loss of natural red/pink pigment (primary)
        - Under-eye darkness: poor oxygenation shows as dark bluish circles (primary)
        - Compared against the forehead baseline if available
        """

        score = 0

        # ── Lip Pallor ─────────────────────────────────────────────────────
        # Anemic lips lose red saturation compared to healthy pink lips
        print(f"\n[Anemia Debug] baseline_color: {baseline_color is not None}")
        if lip_color:
            red = lip_color["rgb"]["red"]
            sat = lip_color["hsv"]["saturation"]
            print(f"[Anemia Debug] LIP -> red: {red}, sat: {sat}")

            # Compare to baseline skin tone rednesss if available
            if baseline_color:
                base_red = baseline_color["rgb"]["red"]
                red_deficit = base_red - red  # positive = lips paler than skin
                print(f"[Anemia Debug] LIP -> base_red: {base_red}, red_deficit: {red_deficit}")
                # Smartphones bump saturation. A normal lip is red_deficit ~ -20 
                # If lips are close to skin color (deficit > -5), they are very pale.
                if red_deficit > 5:
                    score += 3
                elif red_deficit > -3:
                    score += 2
            else:
                # Absolute check
                if red < 140:
                    score += 2

            # Low saturation = washed out / pale lips
            if sat < 40:
                score += 2

        # ── Under-Eye Darkness ─────────────────────────────────────────────
        # Dark circles = poor oxygenation; thin skin lets dark blood vessels show
        if under_eye_color and baseline_color:
            # Under-eye lightness vs baseline skin lightness
            eye_l = under_eye_color["lab"]["l"]
            base_l = baseline_color["lab"]["l"]
            darkness = base_l - eye_l  # positive = under-eye darker than forehead
            print(f"[Anemia Debug] EYE -> base_l: {base_l}, eye_l: {eye_l}, darkness: {darkness}")

            # Phone cameras auto-brighten shadows. Normal non-dark circles show darkness ~ -5
            # If darkness is near 0 or positive, the eyes are unusually dark.
            if darkness > 4:
                score += 3
            elif darkness > 1:
                score += 2
            elif darkness > -1:
                score += 1

            # Bluish hue under eyes (deoxygenated blood tint)
            eye_a = under_eye_color["lab"]["a"]
            print(f"[Anemia Debug] EYE -> eye_a (low is blue/green, high is red): {eye_a}")
            if eye_a < 120:  # low a* = less red/more green-blue
                score += 1

        elif under_eye_color:
            # No baseline — absolute darkness heuristic
            if under_eye_color["lab"]["l"] < 100:
                score += 2

        return min(score, 10)

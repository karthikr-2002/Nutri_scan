"""
Risk Assessor — Calculates final risk level and generates personalized recommendations
"""


class RiskAssessor:
    """
    Calculates a final GREEN/YELLOW/RED risk level from:
    - Jaundice score
    - Vitamin deficiency score
    - Anemia score
    """

    # ==========================================
    # RECOMMENDATIONS DATABASE
    # ==========================================
    RECOMMENDATIONS = {

        'jaundice': {
            'dietary': [
                'Stay well-hydrated — drink at least 8-10 glasses of water daily',
                'Eat a liver-friendly diet: oatmeal, garlic, green tea, leafy greens, avocados',
                'Avoid alcohol completely — it directly damages liver function',
                'Reduce fatty and fried foods that strain the liver',
            ],
            'lifestyle': [
                'Get adequate rest — the liver repairs during sleep',
                'Avoid self-medicating; some drugs worsen liver stress',
                'Maintain a healthy weight to reduce fatty liver risk',
            ],
            'medical': [
                '⚠️ URGENT: Consult a doctor immediately for Liver Function Tests (LFT)',
                'Get tested for hepatitis A, B, and C',
                'An abdominal ultrasound may be required',
                'Do not delay — jaundice may indicate serious liver conditions',
            ],
        },

        'anemia': {
            'dietary': [
                'Eat iron-rich foods: red meat, spinach, lentils, kidney beans, tofu, pumpkin seeds',
                'Pair iron-rich foods with Vitamin C (citrus, tomatoes) to boost absorption',
                'Avoid drinking tea or coffee with meals — tannins block iron absorption',
                'Include folate-rich foods: broccoli, leafy greens, fortified cereals',
                'Eat liver or organ meats once or twice a week for dense iron and B12',
            ],
            'lifestyle': [
                'Avoid strenuous exercise until anemia is treated — conserve energy',
                'Dress warmly in cool environments to manage poor circulation symptoms',
                'Avoid donating blood until hemoglobin levels normalize',
            ],
            'medical': [
                '⚠️ IMPORTANT: Get a Complete Blood Count (CBC) test to confirm anemia',
                'Ask your doctor about iron or B12 supplementation dosage',
                'If iron-deficiency anemia is confirmed, IV iron may be needed in severe cases',
                'Women with heavy periods should discuss blood loss management with a gynecologist',
            ],
        },
    }

    # ==========================================
    # FINAL RISK CALCULATION
    # ==========================================
    def calculate_final_risk(self, combined_scores):
        """
        Args:
            combined_scores: {
                'jaundice': int (0-10),
                'anemia': int (0-10)
            }
        """

        jaundice_score = combined_scores.get('jaundice', 0)
        anemia_score = combined_scores.get('anemia', 0)

        # Jaundice is medically most urgent
        if jaundice_score >= 6:
            return {
                'risk_level': 'RED',
                'risk_label': 'High Risk',
                'risk_description': 'Possible jaundice detected. Immediate medical consultation is strongly recommended.',
                'overall_score': max(jaundice_score, anemia_score),
                'detected_conditions': ['Jaundice'] if jaundice_score >= 3 else [],
            }

        # Anemia also urgent at high scores
        if anemia_score >= 6:
            return {
                'risk_level': 'RED',
                'risk_label': 'High Risk',
                'risk_description': 'Possible anemia indicated. A blood test (CBC) is strongly recommended.',
                'overall_score': max(jaundice_score, anemia_score),
                'detected_conditions': ['Anemia'],
            }

        overall_score = round(max(jaundice_score, anemia_score), 1)

        detected = []
        if jaundice_score >= 3:
            detected.append('Jaundice')
        if anemia_score >= 3:
            detected.append('Anemia')

        # Traffic-light logic
        if overall_score >= 6:
            risk_level = 'RED'
            description = 'Significant health indicators detected. Medical consultation is recommended.'
        elif overall_score >= 3:
            risk_level = 'YELLOW'
            description = 'Some nutritional indicators detected. Lifestyle and dietary improvements are advised.'
        else:
            risk_level = 'GREEN'
            description = 'No significant deficiency indicators detected. Maintain a healthy lifestyle.'

        return {
            'risk_level': risk_level,
            'risk_label': 'High Risk' if risk_level == 'RED'
                         else 'Moderate Risk' if risk_level == 'YELLOW'
                         else 'Low Risk',
            'risk_description': description,
            'overall_score': overall_score,
            'detected_conditions': detected,
        }

    # ==========================================
    # GENERATE RECOMMENDATIONS
    # ==========================================
    def get_recommendations(self, combined_scores, risk_level):

        dietary = []
        lifestyle = []
        medical = []

        general = [
            'Maintain a balanced diet covering all major food groups',
            'Exercise for at least 30 minutes most days of the week',
            'Get 7-8 hours of quality sleep daily',
            'Schedule annual health check-ups',
        ]

        threshold = 3 if risk_level != 'GREEN' else 6

        for condition, score in combined_scores.items():
            if score >= threshold:
                recs = self.RECOMMENDATIONS.get(condition, {})
                dietary.extend(recs.get('dietary', []))
                lifestyle.extend(recs.get('lifestyle', []))
                medical.extend(recs.get('medical', []))

        # Remove duplicates
        dietary = list(dict.fromkeys(dietary))[:6]
        lifestyle = list(dict.fromkeys(lifestyle))[:5]
        medical = list(dict.fromkeys(medical))[:4]

        if risk_level == 'GREEN':
            medical = ['No immediate medical intervention required. Continue routine health monitoring.']

        return {
            'dietary': dietary or ['Maintain a varied and nutrient-rich diet.'],
            'lifestyle': lifestyle or ['Continue healthy daily habits.'],
            'medical': medical,
            'general': general,
        }
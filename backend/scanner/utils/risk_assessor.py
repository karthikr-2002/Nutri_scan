"""
Risk Assessor — Calculates final risk level and generates personalized recommendations
"""


class RiskAssessor:
    """
    Calculates a final GREEN/YELLOW/RED risk level from combined scores
    and generates personalized dietary, lifestyle, and medical recommendations.
    """

    # Recommendations database per condition and risk level
    RECOMMENDATIONS = {
        'anemia': {
            'dietary': [
                'Eat iron-rich foods: red meat, chicken, fish, lentils, spinach, tofu, and fortified cereals',
                'Combine iron-rich foods with Vitamin C (oranges, tomatoes, bell peppers) to enhance absorption',
                'Avoid tea, coffee, and calcium-rich foods within 1 hour of iron-rich meals',
                'Consider iron-fortified breakfast cereals as a daily habit',
            ],
            'lifestyle': [
                'Avoid strenuous activity until iron levels are checked',
                'Get adequate rest; iron deficiency causes fatigue',
                'Cook in cast-iron cookware to add small amounts of iron to food',
            ],
            'medical': [
                'Get a Complete Blood Count (CBC) test to confirm hemoglobin levels',
                'Consult a doctor about iron supplementation if dietary changes are insufficient',
                'Rule out internal bleeding or absorption disorders with a physician',
            ],
        },
        'jaundice': {
            'dietary': [
                'Stay well-hydrated — drink at least 8-10 glasses of water daily',
                'Eat a liver-friendly diet: oatmeal, garlic, green tea, leafy greens, avocados',
                'Avoid alcohol entirely — it directly damages liver function',
                'Reduce fatty and fried foods that put extra stress on the liver',
            ],
            'lifestyle': [
                'Get adequate rest — the liver repairs itself during sleep',
                'Avoid self-medicating; some OTC drugs can worsen liver stress',
                'Maintain a healthy body weight to reduce fatty liver risk',
            ],
            'medical': [
                '⚠️ URGENT: Consult a doctor immediately for liver function tests (LFT)',
                'Get tested for hepatitis A, B, and C',
                'Ultrasound of the abdomen may be recommended to check the liver and gallbladder',
                'Do not delay — jaundice can indicate serious liver or blood conditions',
            ],
        },
        'dehydration': {
            'dietary': [
                'Drink 8-10 glasses (2-2.5 litres) of water daily',
                'Eat water-rich foods: cucumbers, watermelon, oranges, strawberries, lettuce',
                'Include electrolyte drinks (coconut water, ORS) if exercising or sweating heavily',
                'Reduce caffeine and alcohol, which act as diuretics',
            ],
            'lifestyle': [
                'Set hourly reminders to drink water throughout the day',
                'Carry a water bottle at all times',
                'Monitor urine color — pale yellow indicates good hydration',
                'Increase water intake in hot weather or during physical activity',
            ],
            'medical': [
                'If dizziness, rapid heartbeat, or confusion occur, seek immediate medical help',
                'Severe dehydration may require IV fluid therapy',
            ],
        },
        'vitamin': {
            'dietary': [
                'Eat a diverse diet with fruits, vegetables, whole grains, and lean protein',
                'Vitamin D: fatty fish (salmon, tuna), egg yolks, fortified milk',
                'Vitamin B12: meat, dairy, eggs, or fortified plant-based foods',
                'Vitamin C: citrus fruits, bell peppers, kiwi, broccoli',
                'Folate: leafy greens, beans, lentils, asparagus',
            ],
            'lifestyle': [
                'Get 15-30 minutes of sunlight daily for natural Vitamin D synthesis',
                'Exercise regularly to improve nutrient absorption and metabolism',
                'Avoid smoking — it depletes Vitamin C and other antioxidants',
            ],
            'medical': [
                'Get a blood test to identify specific vitamin deficiencies',
                'Discuss vitamin supplementation with a healthcare provider',
                'B12 injections may be needed for severe B12 deficiency',
            ],
        },
    }

    def calculate_final_risk(self, combined_scores):
        """
        Calculate overall risk level from combined condition scores.

        Args:
            combined_scores: dict with anemia, jaundice, dehydration, vitamin scores (0-10)

        Returns:
            dict: {
                'risk_level': 'GREEN' | 'YELLOW' | 'RED',
                'risk_label': str,
                'risk_description': str,
                'overall_score': float,
                'detected_conditions': list,
            }
        """
        scores = [
            combined_scores.get('anemia', 0),
            combined_scores.get('jaundice', 0),
            combined_scores.get('dehydration', 0),
            combined_scores.get('vitamin', 0),
        ]

        # Jaundice gets extra weight as it's the most urgent
        weighted_avg = (
            combined_scores.get('anemia', 0) * 1.0 +
            combined_scores.get('jaundice', 0) * 1.5 +
            combined_scores.get('dehydration', 0) * 0.8 +
            combined_scores.get('vitamin', 0) * 0.7
        ) / 4.0

        overall_score = round(min(10, weighted_avg), 1)

        # Determine detected conditions (score >= 3)
        condition_names = {
            'anemia': 'Anemia (Iron Deficiency)',
            'jaundice': 'Jaundice',
            'dehydration': 'Dehydration',
            'vitamin': 'Vitamin Deficiency',
        }
        detected = [
            condition_names[c] for c, s in combined_scores.items() if s >= 3
        ]

        # Immediate RED if jaundice score is high
        if combined_scores.get('jaundice', 0) >= 5:
            return {
                'risk_level': 'RED',
                'risk_label': 'High Risk',
                'risk_description': 'Possible jaundice detected. Immediate medical consultation is strongly recommended.',
                'overall_score': overall_score,
                'detected_conditions': detected,
            }

        # Traffic light thresholds
        if overall_score >= 5:
            return {
                'risk_level': 'RED',
                'risk_label': 'High Risk',
                'risk_description': 'Multiple or significant nutritional indicators detected. Please consult a healthcare professional.',
                'overall_score': overall_score,
                'detected_conditions': detected,
            }
        elif overall_score >= 2.5:
            return {
                'risk_level': 'YELLOW',
                'risk_label': 'Moderate Risk',
                'risk_description': 'Some nutritional indicators detected. Lifestyle and dietary improvements are advised.',
                'overall_score': overall_score,
                'detected_conditions': detected,
            }
        else:
            return {
                'risk_level': 'GREEN',
                'risk_label': 'Low Risk',
                'risk_description': 'No significant nutritional deficiency indicators detected. Maintain your healthy lifestyle.',
                'overall_score': overall_score,
                'detected_conditions': detected,
            }

    def get_recommendations(self, combined_scores, risk_level):
        """
        Generator personalized recommendations based on conditions and risk.

        Args:
            combined_scores: dict with condition scores
            risk_level: 'GREEN' | 'YELLOW' | 'RED'

        Returns:
            dict: {
                'dietary': list,
                'lifestyle': list,
                'medical': list,
                'hydration': list,
                'general': list,
            }
        """
        dietary = []
        lifestyle = []
        medical = []
        hydration = [
            'Drink at least 8 glasses (2 litres) of water daily',
            'Include hydrating foods like cucumber, watermelon, and oranges in your diet',
        ]
        general = [
            'Get regular health check-ups at least once a year',
            'Maintain a balanced diet with variety across all food groups',
            'Exercise for at least 30 minutes on most days of the week',
            'Get 7-8 hours of quality sleep every night',
        ]

        threshold = 3 if risk_level != 'GREEN' else 5

        for condition, score in combined_scores.items():
            if score >= threshold:
                recs = self.RECOMMENDATIONS.get(condition, {})
                dietary.extend(recs.get('dietary', []))
                lifestyle.extend(recs.get('lifestyle', []))
                medical.extend(recs.get('medical', []))

        # Deduplicate
        dietary = list(dict.fromkeys(dietary))[:6]
        lifestyle = list(dict.fromkeys(lifestyle))[:5]
        medical = list(dict.fromkeys(medical))[:4]

        if risk_level == 'GREEN':
            medical = ['No immediate medical intervention required. Continue routine check-ups.']

        return {
            'dietary': dietary or ['Maintain a balanced, varied diet with all food groups'],
            'lifestyle': lifestyle or ['Maintain regular physical activity and adequate sleep'],
            'medical': medical,
            'hydration': hydration,
            'general': general,
        }

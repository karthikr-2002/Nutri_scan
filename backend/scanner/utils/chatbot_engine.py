"""
Chatbot Engine — Context-aware Q&A based on visual analysis results
"""


class ChatbotEngine:
    """
    Generates relevant questions based on visual scan results and
    evaluates user answers to validate or refine visual findings.
    """

    # Question bank per condition
    QUESTIONS = {
        'anemia': [
            {
                'id': 'anemia_1',
                'question': 'Do you often feel unusually tired or fatigued even after adequate rest?',
                'options': ['Yes, frequently', 'Sometimes', 'Rarely', 'No'],
                'weights': [3, 2, 1, 0]
            },
            {
                'id': 'anemia_2',
                'question': 'Have you noticed paleness in your skin, nails, or the inside of your lower eyelid?',
                'options': ['Yes, clearly visible', 'Slightly', 'Not sure', 'No'],
                'weights': [3, 2, 1, 0]
            },
            {
                'id': 'anemia_3',
                'question': 'Do you experience shortness of breath during light physical activity?',
                'options': ['Yes, frequently', 'Sometimes', 'Rarely', 'No'],
                'weights': [3, 2, 1, 0]
            },
            {
                'id': 'anemia_4',
                'question': 'How often do you consume iron-rich foods (meat, spinach, lentils, beans)?',
                'options': ['Daily', 'Few times a week', 'Rarely', 'Almost never'],
                'weights': [0, 1, 2, 3]
            },
        ],
        'jaundice': [
            {
                'id': 'jaundice_1',
                'question': 'Have you noticed any yellowish tint in your eyes or skin recently?',
                'options': ['Yes, clearly', 'Slightly', 'Not sure', 'No'],
                'weights': [4, 2, 1, 0]
            },
            {
                'id': 'jaundice_2',
                'question': 'Have you experienced dark-colored urine or pale-colored stools recently?',
                'options': ['Yes', 'Not sure', 'No'],
                'weights': [3, 1, 0]
            },
            {
                'id': 'jaundice_3',
                'question': 'Do you have any history of liver disease, hepatitis, or gallstones?',
                'options': ['Yes', 'Not sure', 'No'],
                'weights': [3, 1, 0]
            },
            {
                'id': 'jaundice_4',
                'question': 'Have you consumed alcohol heavily in the past week?',
                'options': ['Yes, heavily', 'Moderately', 'A little', 'No'],
                'weights': [3, 2, 1, 0]
            },
        ],
        'dehydration': [
            {
                'id': 'dehydration_1',
                'question': 'How many glasses of water do you drink per day on average?',
                'options': ['8+ glasses', '5-7 glasses', '3-4 glasses', 'Less than 3'],
                'weights': [0, 1, 2, 3]
            },
            {
                'id': 'dehydration_2',
                'question': 'Do you experience dry mouth, chapped lips, or dry skin frequently?',
                'options': ['Yes, very often', 'Sometimes', 'Rarely', 'No'],
                'weights': [3, 2, 1, 0]
            },
            {
                'id': 'dehydration_3',
                'question': 'Do you often feel dizzy, lightheaded, or have headaches?',
                'options': ['Yes, often', 'Sometimes', 'Rarely', 'No'],
                'weights': [3, 2, 1, 0]
            },
            {
                'id': 'dehydration_4',
                'question': 'Is your urine usually dark yellow or amber colored?',
                'options': ['Yes, dark', 'Light yellow', 'Clear/Pale', "I don't notice"],
                'weights': [3, 1, 0, 1]
            },
        ],
        'vitamin': [
            {
                'id': 'vitamin_1',
                'question': 'Do you experience frequent mouth sores, cracked corners of lips, or a sore tongue?',
                'options': ['Yes, often', 'Occasionally', 'Rarely', 'No'],
                'weights': [3, 2, 1, 0]
            },
            {
                'id': 'vitamin_2',
                'question': 'Do you get adequate sunlight exposure (at least 15-30 minutes daily)?',
                'options': ['Yes, daily', 'Few times a week', 'Rarely', 'Almost never'],
                'weights': [0, 1, 2, 3]
            },
            {
                'id': 'vitamin_3',
                'question': 'Do you consume fruits and vegetables regularly?',
                'options': ['Multiple servings daily', 'Once a day', 'Occasionally', 'Rarely'],
                'weights': [0, 1, 2, 3]
            },
            {
                'id': 'vitamin_4',
                'question': 'Have you noticed slow wound healing, brittle hair/nails, or dry scaly skin?',
                'options': ['Yes, clearly', 'Somewhat', 'Rarely', 'No'],
                'weights': [3, 2, 1, 0]
            },
        ],
    }

    # ─────────────────────────────────────────────

    def get_questions(self, visual_analysis):

        questions = []
        threshold = 2

        condition_map = {
            'anemia': visual_analysis.get('anemia_score', 0),
            'jaundice': visual_analysis.get('jaundice_score', 0),
            'dehydration': visual_analysis.get('dehydration_score', 0),
            'vitamin': visual_analysis.get('vitamin_score', 0),
        }

        sorted_conditions = sorted(condition_map.items(), key=lambda x: x[1], reverse=True)

        for condition, score in sorted_conditions:
            if score >= threshold:
                condition_questions = self.QUESTIONS.get(condition, [])
                for q in condition_questions:  # ASK ALL QUESTIONS
                    q_copy = q.copy()
                    q_copy['condition'] = condition
                    q_copy['visual_score'] = score
                    questions.append(q_copy)

        if not questions:
            for condition in ['dehydration', 'vitamin']:
                for q in self.QUESTIONS[condition][:2]:
                    q_copy = q.copy()
                    q_copy['condition'] = condition
                    q_copy['visual_score'] = 0
                    questions.append(q_copy)

        return questions

    # ─────────────────────────────────────────────

    def evaluate_answers(self, visual_analysis, answers):

        chatbot_scores = {
            'anemia': 0,
            'jaundice': 0,
            'dehydration': 0,
            'vitamin': 0,
        }

        all_questions = {}
        for condition, questions in self.QUESTIONS.items():
            for q in questions:
                all_questions[q['id']] = (condition, q['weights'])

        max_possible_scores = {
            'anemia': 0,
            'jaundice': 0,
            'dehydration': 0,
            'vitamin': 0,
        }

        for qid, answer_index in answers.items():
            if qid not in all_questions:
                continue

            condition, weights = all_questions[qid]

            if 0 <= answer_index < len(weights):
                chatbot_scores[condition] += weights[answer_index]
                max_possible_scores[condition] += max(weights)

        # ✅ FIXED NORMALIZATION (dynamic max weight)
        for condition in chatbot_scores:
            if max_possible_scores[condition] > 0:
                chatbot_scores[condition] = round(
                    min(10, (chatbot_scores[condition] / max_possible_scores[condition]) * 10),
                    1
                )

        visual = {
            'anemia': visual_analysis.get('anemia_score', 0),
            'jaundice': visual_analysis.get('jaundice_score', 0),
            'dehydration': visual_analysis.get('dehydration_score', 0),
            'vitamin': visual_analysis.get('vitamin_score', 0),
        }

        combined_scores = {}

        for condition in chatbot_scores:
            if max_possible_scores[condition] > 0:
                combined = (visual[condition] * 0.6) + (chatbot_scores[condition] * 0.4)
            else:
                combined = visual[condition]

            combined_scores[condition] = round(min(10, combined), 1)

        return {
            'condition_scores': visual,
            'chatbot_scores': chatbot_scores,
            'combined_scores': combined_scores,
        }
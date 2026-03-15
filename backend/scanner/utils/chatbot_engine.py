"""
Chatbot Engine — Context-aware Q&A based on triggered conditions
"""


class ChatbotEngine:
    """
    Generates relevant questions based on triggered conditions
    and evaluates user answers to refine visual findings.
    """

    # ==========================================
    # QUESTION BANK
    # ==========================================
    QUESTIONS = {

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



        'anemia': [
            {
                'id': 'anemia_1',
                'question': 'Do you frequently feel unusually tired, weak, or short of breath during normal activities?',
                'options': ['Yes, very often', 'Sometimes', 'Rarely', 'No'],
                'weights': [4, 2, 1, 0]
            },
            {
                'id': 'anemia_2',
                'question': 'Are your hands or feet often unusually cold, even in warm conditions?',
                'options': ['Yes, frequently', 'Occasionally', 'Rarely', 'No'],
                'weights': [3, 2, 1, 0]
            },
            {
                'id': 'anemia_3',
                'question': 'Do you experience dizziness, lightheadedness, or frequent headaches?',
                'options': ['Yes, frequently', 'Sometimes', 'Rarely', 'No'],
                'weights': [3, 2, 1, 0]
            },
            {
                'id': 'anemia_4',
                'question': 'Is your diet low in iron-rich foods (red meat, leafy greens, legumes)?',
                'options': ['Very low (vegetarian/vegan, no supplements)', 'Somewhat low', 'Moderate', 'High'],
                'weights': [3, 2, 1, 0]
            },
        ],
    }

    # ==========================================
    # GET QUESTIONS (TRIGGER-BASED)
    # ==========================================
    def get_questions(self, trigger_conditions):
        """
        trigger_conditions = ['jaundice', 'anemia']
        Only ask questions for conditions that passed threshold.
        """

        questions = []

        for condition in trigger_conditions:
            if condition in self.QUESTIONS:
                for q in self.QUESTIONS[condition]:
                    q_copy = q.copy()
                    q_copy['condition'] = condition
                    questions.append(q_copy)

        return questions

    # ==========================================
    # EVALUATE ANSWERS
    # ==========================================
    def evaluate_answers(self, visual_analysis, answers):

        chatbot_scores = {
            'jaundice': 0,
            'anemia': 0,
        }

        max_possible = {
            'jaundice': 0,
            'anemia': 0,
        }

        # Build lookup
        all_questions = {}
        for condition, questions in self.QUESTIONS.items():
            for q in questions:
                all_questions[q['id']] = (condition, q['weights'])

        # Calculate chatbot score
        for qid, answer_index in answers.items():

            if qid not in all_questions:
                continue

            condition, weights = all_questions[qid]

            if 0 <= answer_index < len(weights):
                chatbot_scores[condition] += weights[answer_index]
                max_possible[condition] += max(weights)

        # Normalize chatbot score to 0–10
        for condition in chatbot_scores:
            if max_possible[condition] > 0:
                chatbot_scores[condition] = round(
                    (chatbot_scores[condition] / max_possible[condition]) * 10,
                    1
                )

        # Visual scores
        visual = {
            'jaundice': visual_analysis.get('jaundice_score', 0),
            'anemia': visual_analysis.get('anemia_score', 0),
        }

        # ==========================================
        # COMBINE VISUAL + CHATBOT
        # ==========================================
        combined_scores = {}

        for condition in visual:

            if max_possible.get(condition, 0) > 0:
                if condition == 'jaundice':
                    # Equal weight: visual scan + chatbot symptoms
                    combined = (visual[condition] * 0.5) + (chatbot_scores.get(condition, 0) * 0.5)
                elif condition == 'anemia':
                    # Camera is unreliable for anemia — symptoms are far more definitive
                    combined = (visual[condition] * 0.3) + (chatbot_scores.get(condition, 0) * 0.7)
                else:
                    combined = visual[condition]
            else:
                combined = visual[condition]

            combined_scores[condition] = round(min(10, combined), 1)

        return {
            'visual_scores': visual,
            'chatbot_scores': chatbot_scores,
            'combined_scores': combined_scores,
        }
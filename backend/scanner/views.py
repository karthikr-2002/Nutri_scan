from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import HttpResponse

from .models import ScanSession
from .serializers import ScanSessionSerializer
from .utils.face_detector import FaceDetector
from .utils.feature_analyzer import FeatureAnalyzer
from .utils.chatbot_engine import ChatbotEngine
from .utils.risk_assessor import RiskAssessor
from .utils.report_generator import ReportGenerator


# ============================================================
# IMAGE UPLOAD + VISUAL ANALYSIS
# ============================================================

@api_view(['POST'])
def upload_image(request):
    """
    Upload image, detect face, perform visual analysis,
    and return scan session with conditional chatbot questions.
    """

    if 'image' not in request.FILES:
        return Response(
            {'error': 'No image provided'},
            status=status.HTTP_400_BAD_REQUEST
        )

    scan_session = ScanSession.objects.create(
        original_image=request.FILES['image']
    )

    image_path = scan_session.original_image.path

    try:
        face_detector = FaceDetector()
    except Exception as e:
        scan_session.delete()
        return Response(
            {'error': f'Failed to initialize face detector: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    feature_analyzer = FeatureAnalyzer()

    face_result = face_detector.detect_face(image_path)
    scan_session.face_detected = face_result['face_detected']

    visual_analysis = {
        'jaundice_score': 0,
        'anemia_score': 0,
    }

    # ========================================================
    # IF FACE DETECTED → RUN ANALYSIS
    # ========================================================
    if face_result['face_detected']:

        landmarks = face_result['landmarks']

        # -----------------------------
        # Forehead Baseline Extraction
        # -----------------------------
        forehead_roi = face_detector.extract_roi(image_path, landmarks, 'forehead')
        forehead_color = None

        if forehead_roi is not None:
            forehead_color = feature_analyzer.analyze_color(forehead_roi)

        # -----------------------------
        # Cheeks → Jaundice Detection
        # -----------------------------
        cheek_yellow_score = 0

        for cheek in ['left_cheek', 'right_cheek']:
            cheek_roi = face_detector.extract_roi(image_path, landmarks, cheek)

            if cheek_roi is not None:
                cheek_color = feature_analyzer.analyze_color(cheek_roi)

                if cheek_color:
                    # check_jaundice(sclera_color, skin_color) — uses cheek as
                    # primary colour and forehead as the baseline skin reference
                    cheek_yellow_score = max(
                        cheek_yellow_score,
                        feature_analyzer.check_jaundice(
                            cheek_color,
                            forehead_color or cheek_color
                        )
                    )

        visual_analysis['jaundice_score'] = round(
            cheek_yellow_score * 0.4,
            1
        )
        # -----------------------------
        # Lips → Anemia Support
        # -----------------------------
        best_lip_color = None

        for lip_region in ['upper_lip', 'lower_lip']:
            lip_roi = face_detector.extract_roi(image_path, landmarks, lip_region)
            if lip_roi is not None:
                lip_color = feature_analyzer.analyze_color(lip_roi)
                if lip_color:
                    # Capture the first valid lip color for Anemia check
                    best_lip_color = lip_color
                    break

        # -----------------------------
        # Under-Eyes + Lips → Anemia Detection
        # -----------------------------
        best_under_eye_color = None

        for eye_region in ['left_under_eye', 'right_under_eye']:
            eye_roi = face_detector.extract_roi(image_path, landmarks, eye_region)
            if eye_roi is not None:
                eye_color = feature_analyzer.analyze_color(eye_roi)
                if eye_color:
                    if best_under_eye_color is None:
                        best_under_eye_color = eye_color
                    else:
                        # Pick the darker of the two sides (stronger anemia signal)
                        if eye_color['lab']['l'] < best_under_eye_color['lab']['l']:
                            best_under_eye_color = eye_color

        anemia_score = feature_analyzer.check_anemia(
            lip_color=best_lip_color,
            under_eye_color=best_under_eye_color,
            baseline_color=forehead_color
        )
        visual_analysis['anemia_score'] = round(anemia_score, 1)

    # Save visual analysis
    scan_session.visual_analysis = visual_analysis
    scan_session.save()

    # ========================================================
    # THRESHOLD-BASED CHATBOT TRIGGER
    # ========================================================
    chatbot_engine = ChatbotEngine()

    THRESHOLD = 2
    trigger_conditions = []

    if visual_analysis.get('jaundice_score', 0) > THRESHOLD:
        trigger_conditions.append('jaundice')

    if visual_analysis.get('anemia_score', 0) > THRESHOLD:
        trigger_conditions.append('anemia')

    questions = chatbot_engine.get_questions(trigger_conditions)

    serializer = ScanSessionSerializer(scan_session)
    response_data = serializer.data
    response_data['chatbot_questions'] = questions
    response_data['face_detection_message'] = face_result.get('message', '')

    return Response(response_data, status=status.HTTP_201_CREATED)


# ============================================================
# SUBMIT CHATBOT ANSWERS
# ============================================================

@api_view(['POST'])
def submit_chatbot(request):
    session_id = request.data.get('session_id')
    answers = request.data.get('answers', {})

    if not session_id:
        return Response(
            {'error': 'session_id is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        scan_session = ScanSession.objects.get(session_id=session_id)
    except ScanSession.DoesNotExist:
        return Response(
            {'error': 'Scan session not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    visual_analysis = scan_session.visual_analysis or {
        'jaundice_score': 0,
        'anemia_score': 0
    }

    chatbot_engine = ChatbotEngine()
    evaluation = chatbot_engine.evaluate_answers(visual_analysis, answers)

    risk_assessor = RiskAssessor()
    risk_data = risk_assessor.calculate_final_risk(
        evaluation['combined_scores']
    )

    recommendations = risk_assessor.get_recommendations(
        evaluation['combined_scores'],
        risk_data['risk_level']
    )

    scan_session.chatbot_responses = answers
    scan_session.final_risk_level = risk_data['risk_level']
    scan_session.combined_score = int(risk_data['overall_score'] * 10)

    scan_session.visual_analysis = {
        **visual_analysis,
        'combined_scores': evaluation['combined_scores'],
    }

    scan_session.save()

    return Response({
        'session_id': str(scan_session.session_id),
        'evaluation': evaluation,
        'risk': risk_data,
        'recommendations': recommendations,
    })


# ============================================================
# PDF REPORT GENERATION
# ============================================================

@api_view(['GET'])
def get_report(request, session_id):

    try:
        scan_session = ScanSession.objects.get(session_id=session_id)
    except ScanSession.DoesNotExist:
        return Response(
            {'error': 'Scan session not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    if not scan_session.final_risk_level:
        return Response(
            {'error': 'Scan analysis not complete. Please complete chatbot first.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    visual_analysis = scan_session.visual_analysis or {}

    combined_scores = visual_analysis.pop('combined_scores', {
        'jaundice': visual_analysis.get('jaundice_score', 0),
        'anemia': visual_analysis.get('anemia_score', 0),
    })

    risk_assessor = RiskAssessor()
    risk_data = risk_assessor.calculate_final_risk(combined_scores)

    recommendations = risk_assessor.get_recommendations(
        combined_scores,
        risk_data['risk_level']
    )

    session_data = {
        'session_id': scan_session.session_id,
        'created_at': scan_session.created_at,
        'visual_analysis': visual_analysis,
        'combined_scores': combined_scores,
    }

    generator = ReportGenerator()
    pdf_bytes = generator.generate_pdf(
        session_data,
        risk_data,
        recommendations
    )

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = (
        f'attachment; filename="nutriscan-report-{str(scan_session.session_id)[:8]}.pdf"'
    )
    response['Access-Control-Expose-Headers'] = 'Content-Disposition'

    return response


# ============================================================
# GET SCAN DETAILS
# ============================================================

@api_view(['GET'])
def get_scan(request, session_id):
    try:
        scan_session = ScanSession.objects.get(session_id=session_id)
        serializer = ScanSessionSerializer(scan_session)
        return Response(serializer.data)
    except ScanSession.DoesNotExist:
        return Response(
            {'error': 'Scan not found'},
            status=status.HTTP_404_NOT_FOUND
        )


# ============================================================
# API TEST
# ============================================================

@api_view(['GET'])
def test_api(request):
    return Response({
        'message': 'Nutri-Scan API is working!',
        'version': '3.1 (Threshold-Based Chatbot Enabled)',
    })
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


@api_view(['POST'])
def upload_image(request):
    """
    Upload image, detect face, perform visual analysis, and return scan session.
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
        'anemia_score': 0,
        'jaundice_score': 0,
        'dehydration_score': 0,
        'vitamin_score': 0
    }

    if face_result['face_detected']:
        landmarks = face_result['landmarks']
        analysis_results = {}

        # ===============================
        # Forehead Baseline Extraction
        # ===============================
        forehead_roi = face_detector.extract_roi(image_path, landmarks, 'forehead')
        forehead_color = None
        if forehead_roi is not None:
            forehead_color = feature_analyzer.analyze_color(forehead_roi)

        # ===============================
        # EYES (Anemia + Jaundice)
        # ===============================
        left_eye_roi = face_detector.extract_roi(image_path, landmarks, 'left_eye')
        right_eye_roi = face_detector.extract_roi(image_path, landmarks, 'right_eye')

        eye_pallor_score = 0
        eye_yellow_score = 0

        for eye_roi in [left_eye_roi, right_eye_roi]:
            if eye_roi is not None:
                eye_color = feature_analyzer.analyze_color(eye_roi)
                if eye_color:
                    eye_pallor_score = max(
                        eye_pallor_score,
                        feature_analyzer.check_pallor(
                            eye_color,
                            baseline_data=forehead_color
                        )
                    )
                    eye_yellow_score = max(
                        eye_yellow_score,
                        feature_analyzer.check_yellowness(
                            eye_color,
                            baseline_data=forehead_color
                        )
                    )

        analysis_results['eyes'] = {
            'pallor_score': eye_pallor_score,
            'yellow_score': eye_yellow_score,
        }

        # ===============================
        # LIPS (Anemia + Dehydration + Vitamin)
        # ===============================
        upper_lip_roi = face_detector.extract_roi(image_path, landmarks, 'upper_lip')
        lower_lip_roi = face_detector.extract_roi(image_path, landmarks, 'lower_lip')

        lip_pallor_score = 0
        lip_dryness_score = 0
        best_lip_color = None
        best_lip_texture = None

        for lip_roi in [upper_lip_roi, lower_lip_roi]:
            if lip_roi is not None:
                lip_color = feature_analyzer.analyze_color(lip_roi)
                lip_texture = feature_analyzer.analyze_texture(lip_roi)

                if lip_color:
                    score = feature_analyzer.check_pallor(
                        lip_color,
                        baseline_data=forehead_color
                    )
                    if score > lip_pallor_score:
                        lip_pallor_score = score
                        best_lip_color = lip_color

                if lip_texture:
                    score = feature_analyzer.check_dryness(lip_texture)
                    if score > lip_dryness_score:
                        lip_dryness_score = score
                        best_lip_texture = lip_texture

        analysis_results['lips'] = {
            'pallor_score': lip_pallor_score,
            'dryness_score': lip_dryness_score,
        }

        # ===============================
        # CHEEKS (Jaundice)
        # ===============================
        cheek_yellow_score = 0
        for cheek in ['left_cheek', 'right_cheek']:
            cheek_roi = face_detector.extract_roi(image_path, landmarks, cheek)
            if cheek_roi is not None:
                cheek_color = feature_analyzer.analyze_color(cheek_roi)
                if cheek_color:
                    cheek_yellow_score = max(
                        cheek_yellow_score,
                        feature_analyzer.check_yellowness(
                            cheek_color,
                            baseline_data=forehead_color
                        )
                    )

        # ===============================
        # FINAL CONDITION SCORES
        # ===============================

        visual_analysis['anemia_score'] = round(
            analysis_results['eyes']['pallor_score'] * 0.4 +
            analysis_results['lips']['pallor_score'] * 0.6,
            1
        )

        visual_analysis['jaundice_score'] = round(
            analysis_results['eyes']['yellow_score'] * 0.6 +
            cheek_yellow_score * 0.4,
            1
        )

        visual_analysis['dehydration_score'] = round(
            analysis_results['lips']['dryness_score'] * 0.8,
            1
        )

        # Vitamin deficiency (NEW — proper method)
        vitamin_score = 0
        if best_lip_color and best_lip_texture:
            vitamin_score = feature_analyzer.check_vitamin_deficiency(
                best_lip_color,
                best_lip_texture,
                baseline_data=forehead_color
            )

        visual_analysis['vitamin_score'] = round(vitamin_score, 1)

        scan_session.visual_analysis = visual_analysis

    scan_session.save()

    # ===============================
    # Chatbot Questions
    # ===============================
    chatbot_engine = ChatbotEngine()
    questions = chatbot_engine.get_questions(visual_analysis)

    serializer = ScanSessionSerializer(scan_session)
    response_data = serializer.data
    response_data['chatbot_questions'] = questions
    response_data['face_detection_message'] = face_result.get('message', '')

    return Response(response_data, status=status.HTTP_201_CREATED)


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
        'anemia_score': 0,
        'jaundice_score': 0,
        'dehydration_score': 0,
        'vitamin_score': 0
    }

    chatbot_engine = ChatbotEngine()
    evaluation = chatbot_engine.evaluate_answers(visual_analysis, answers)

    risk_assessor = RiskAssessor()
    risk_data = risk_assessor.calculate_final_risk(evaluation['combined_scores'])
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
            {'error': 'Scan analysis not complete. Please complete the chatbot first.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    visual_analysis = scan_session.visual_analysis or {}
    combined_scores = visual_analysis.pop('combined_scores', {
        'anemia': visual_analysis.get('anemia_score', 0),
        'jaundice': visual_analysis.get('jaundice_score', 0),
        'dehydration': visual_analysis.get('dehydration_score', 0),
        'vitamin': visual_analysis.get('vitamin_score', 0),
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
    pdf_bytes = generator.generate_pdf(session_data, risk_data, recommendations)

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="nutriscan-report-{str(scan_session.session_id)[:8]}.pdf"'
    response['Access-Control-Expose-Headers'] = 'Content-Disposition'
    return response


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


@api_view(['GET'])
def test_api(request):
    return Response({
        'message': 'Nutri-Scan API is working!',
        'version': '3.0 (Fully Wired)',
    })
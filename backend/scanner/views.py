from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import ScanSession
from .serializers import ScanSessionSerializer

@api_view(['POST'])
def upload_image(request):
    """
    Upload image and create a new scan session
    """
    if 'image' not in request.FILES:
        return Response(
            {'error': 'No image provided'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Create new scan session
    scan_session = ScanSession.objects.create(
        original_image=request.FILES['image']
    )
    
    # Serialize and return
    serializer = ScanSessionSerializer(scan_session)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
def get_scan(request, session_id):
    """
    Get scan session by ID
    """
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
    """
    Test endpoint to verify API is working
    """
    return Response({
        'message': 'Nutri-Scan API is working!',
        'version': '1.0',
        'endpoints': {
            'upload': '/api/upload/',
            'get_scan': '/api/scan/<session_id>/'
        }
    })
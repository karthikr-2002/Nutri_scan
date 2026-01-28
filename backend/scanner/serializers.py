from rest_framework import serializers
from .models import ScanSession

class ScanSessionSerializer(serializers.ModelSerializer):
    """Serializer for ScanSession model"""
    
    class Meta:
        model = ScanSession
        fields = [
            'session_id',
            'created_at',
            'original_image',
            'face_detected',
            'visual_analysis',
            'chatbot_responses',
            'final_risk_level',
            'combined_score'
        ]
        read_only_fields = ['session_id', 'created_at']
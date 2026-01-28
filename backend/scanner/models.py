from django.db import models
from django.utils import timezone
import uuid

class ScanSession(models.Model):
    """Stores each user scan session"""
    
    # Unique identifier
    session_id = models.UUIDField(
        default=uuid.uuid4, 
        editable=False, 
        unique=True
    )
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    
    # Image
    original_image = models.ImageField(upload_to='uploads/')
    
    # Face detection status
    face_detected = models.BooleanField(default=False)
    
    # Visual analysis results (stored as JSON)
    visual_analysis = models.JSONField(null=True, blank=True)
    # Example: {
    #   "anemia_score": 6,
    #   "jaundice_score": 2,
    #   "dehydration_score": 4,
    #   "vitamin_score": 3
    # }
    
    # Chatbot responses
    chatbot_responses = models.JSONField(null=True, blank=True)
    
    # Final risk assessment
    RISK_CHOICES = [
        ('GREEN', 'Low Risk'),
        ('YELLOW', 'Moderate Risk'),
        ('RED', 'High Risk'),
    ]
    final_risk_level = models.CharField(
        max_length=10,
        choices=RISK_CHOICES,
        null=True,
        blank=True
    )
    
    combined_score = models.IntegerField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Scan {self.session_id} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
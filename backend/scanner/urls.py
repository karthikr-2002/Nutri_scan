from django.urls import path
from . import views

urlpatterns = [
    path('api/test/', views.test_api, name='test_api'),
    path('api/upload/', views.upload_image, name='upload_image'),
    path('api/chatbot/', views.submit_chatbot, name='submit_chatbot'),
    path('api/scan/<uuid:session_id>/', views.get_scan, name='get_scan'),
    path('api/report/<uuid:session_id>/', views.get_report, name='get_report'),
]
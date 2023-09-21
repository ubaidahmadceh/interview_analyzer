from django.urls import path
from .views import *

urlpatterns = [
    path('get-user-profiles/', GetUserProfiles.as_view()),
    path('chat/', Chat.as_view()),
    path('get-patterns/', Patterns.as_view()),
    path('overall-analysis/', OverallAnalysis.as_view()),
    path('voice-transcription/', VoiceTranscription.as_view())
]
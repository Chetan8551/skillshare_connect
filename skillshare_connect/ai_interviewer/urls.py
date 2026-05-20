from django.urls import path
from . import views

from .views import (
    interview_page,
    interview_chat
)

urlpatterns = [
    path('', views.interview_page, name='ai_interview'),
    path("chat/", interview_chat, name="interview_chat"),
]
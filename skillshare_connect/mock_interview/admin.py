# skillshare_connect/mock_interview/admin.py
from django.contrib import admin
from .models import InterviewSession

@admin.register(InterviewSession)
class InterviewSessionAdmin(admin.ModelAdmin):
    list_display = ('skill', 'user', 'similarity_score', 'created_at')
    readonly_fields = ('created_at',)

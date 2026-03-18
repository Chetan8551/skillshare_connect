#mock_interview\models.py
from django.db import models
from django.conf import settings

class InterviewSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    skill = models.CharField(max_length=120)
    question = models.TextField()
    reference_answer = models.TextField(blank=True)
    user_answer = models.TextField(blank=True)
    similarity_score = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.skill} @ {self.created_at:%Y-%m-%d %H:%M}"

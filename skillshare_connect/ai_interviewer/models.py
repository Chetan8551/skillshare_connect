from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

from django.db import models

class Interview(models.Model):
    user_name = models.CharField(max_length=100)
    question = models.TextField()
    answer = models.TextField()
    feedback = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
class InterviewSession(models.Model):
    STAGE_CHOICES = [
        ("intro", "Introduction"),
        ("warmup", "Warmup"),
        ("technical_basic", "Technical Basic"),
        ("technical_intermediate", "Technical Intermediate"),
        ("technical_advanced", "Technical Advanced"),
        ("behavioral", "Behavioral"),
        ("final", "Final"),
        ("ended", "Ended"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="interview_sessions",
        null=True,
        blank=True
    )

    role = models.CharField(max_length=255)

    current_stage = models.CharField(
        max_length=50,
        choices=STAGE_CHOICES,
        default="intro"
    )

    started_at = models.DateTimeField(auto_now_add=True)

    ended_at = models.DateTimeField(null=True, blank=True)

    is_active = models.BooleanField(default=True)

    overall_score = models.FloatField(default=0)

    communication_score = models.FloatField(default=0)

    technical_score = models.FloatField(default=0)

    confidence_score = models.FloatField(default=0)

    problem_solving_score = models.FloatField(default=0)

    notes = models.TextField(blank=True)

    mentioned_skills = models.TextField(blank=True)

    weak_topics = models.TextField(blank=True)

    strong_topics = models.TextField(blank=True)

    candidate_summary = models.TextField(blank=True)

    question_count = models.IntegerField(
        default=0
    )

    strong_answer_count = models.IntegerField(
        default=0
    )

    weak_answer_count = models.IntegerField(
        default=0
    )

    conversation_turns = models.IntegerField(
        default=0
    )

    interview_completed = models.BooleanField(
        default=False
    )

    final_feedback = models.TextField(
        blank=True,
        default=""
    )

    final_score = models.FloatField(
        default=0
    )

    def __str__(self):
        return f"{self.role} Interview - {self.id}"


class InterviewQuestion(models.Model):
    session = models.ForeignKey(
        InterviewSession,
        on_delete=models.CASCADE,
        related_name="questions"
    )

    question_text = models.TextField()

    stage = models.CharField(max_length=50)

    difficulty = models.CharField(
        max_length=20,
        default="medium"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.question_text[:50]


class InterviewAnswer(models.Model):
    QUALITY_CHOICES = [
        ("strong", "Strong"),
        ("average", "Average"),
        ("weak", "Weak"),
    ]

    question = models.ForeignKey(
        InterviewQuestion,
        on_delete=models.CASCADE,
        related_name="answers"
    )

    answer_text = models.TextField()

    feedback = models.TextField(blank=True)

    better_answer = models.TextField(blank=True)

    answer_quality = models.CharField(
        max_length=20,
        choices=QUALITY_CHOICES,
        default="average"
    )

    score = models.FloatField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Answer to Question {self.question.id}"
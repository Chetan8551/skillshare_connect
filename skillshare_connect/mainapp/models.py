from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


class CustomUser(AbstractUser):
    university = models.CharField(max_length=100, blank=True)
    year_of_study = models.CharField(max_length=20, choices=[
        ('1st Year', '1st Year'),
        ('2nd Year', '2nd Year'),
        ('3rd Year', '3rd Year'),
        ('4th Year', '4th Year'),
        ('Graduate', 'Graduate'),
    ], blank=True)
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    last_seen = models.DateTimeField(null=True, blank=True)

    @property
    def is_online(self):
        if not self.last_seen:
            return False
        now = timezone.now()
        return now - self.last_seen <= timedelta(minutes=5) 

    def __str__(self):
        return f"{self.username} - {self.university}"


class Skill(models.Model):
    name = models.CharField(max_length=50, unique=True)
    category = models.CharField(max_length=50, choices=[
        ('Technical', 'Technical'),
        ('Creative', 'Creative'),
        ('Language', 'Language'),
        ('Other', 'Other'),
    ])

    def __str__(self):
        return self.name


class UserSkill(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='skills')
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    proficiency = models.CharField(max_length=20, choices=[
        ('Beginner', 'Beginner'),
        ('Intermediate', 'Intermediate'),
        ('Advanced', 'Advanced'),
        ('Expert', 'Expert'),
    ])
    skill_type = models.CharField(max_length=10, choices=[
        ('teach', 'Can Teach'),
        ('learn', 'Wants to Learn'),
    ])
    description = models.TextField(blank=True)
    experience = models.CharField(max_length=50, blank=True)

    class Meta:
        unique_together = ('user', 'skill', 'skill_type')

    def __str__(self):
        return f"{self.user.username} - {self.skill.name} ({self.skill_type})"


class ConnectionRequest(models.Model):
    from_user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sent_requests')
    to_user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='received_requests')
    message = models.TextField(blank=True)
    status = models.CharField(max_length=20, default='pending', choices=[
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('from_user', 'to_user')

    def __str__(self):
        return f"{self.from_user} -> {self.to_user} ({self.status})"


class Session(models.Model):
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='teaching_sessions'
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='learning_sessions'
    )
    skill = models.ForeignKey(Skill, on_delete=models.SET_NULL, null=True, blank=True)
    topic = models.CharField(max_length=200, default="General Session")
    description = models.TextField(blank=True, null=True)
    scheduled_time = models.DateTimeField()
    duration = models.DurationField(default=timedelta(hours=1))
    is_online = models.BooleanField(default=False)
    meeting_link = models.URLField(blank=True, null=True)
    location = models.CharField(max_length=200, blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('scheduled', 'Scheduled'),
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled'),
        ],
        default='scheduled',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    from django.utils import timezone

    @property
    def end_time(self):
        """Return timezone-aware end time."""
        if not self.scheduled_time:
            return None
        st = self.scheduled_time
        if timezone.is_naive(st):
            st = timezone.make_aware(st, timezone.get_default_timezone())
        return st + (self.duration or timedelta())

    def is_active(self):
        return self.end_time and timezone.now() < self.end_time and self.status == 'scheduled'

    def __str__(self):
        return f"{self.topic} - {self.teacher.username} with {self.student.username}"

    def save(self, *args, **kwargs):
        """Ensure DB status is consistent with time."""
        if self.end_time and timezone.now() >= self.end_time and self.status == "scheduled":
            self.status = "completed"
        super().save(*args, **kwargs)



class Review(models.Model):
    session = models.OneToOneField(Session, on_delete=models.CASCADE, related_name='review')
    reviewer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='given_reviews')
    reviewee = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='received_reviews')
    rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.reviewer} -> {self.reviewee} ({self.rating} stars)"


class Availability(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='availability')
    day_of_week = models.PositiveIntegerField(choices=[
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ])
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        unique_together = ('user', 'day_of_week')

    def __str__(self):
        return f"{self.user} - {self.get_day_of_week_display()}: {self.start_time} to {self.end_time}"



class Message(models.Model):
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='received_messages')
    connection = models.ForeignKey(ConnectionRequest, on_delete=models.CASCADE, related_name='messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.sender} to {self.receiver}: {self.content[:50]}"

class PasswordResetOTP(models.Model):
    """
    Store OTPs for password reset (6-digit numeric).
    """
    user = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='password_otps')
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expiry = models.DateTimeField()
    used = models.BooleanField(default=False)

    def is_valid(self):
        return (not self.used) and (timezone.now() < self.expiry)

    def __str__(self):
        return f"OTP for {self.user.email} - {self.code} (used={self.used})"
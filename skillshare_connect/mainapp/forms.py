from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from mainapp.models import CustomUser, UserSkill, Skill, ConnectionRequest, Session, Availability, Message

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ("username", "first_name", "last_name", "email", "city", "university", "year_of_study", "bio")

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ("username", "first_name", "last_name", "email", "city", "university", "year_of_study", "bio")

class UserSkillForm(forms.ModelForm):
    class Meta:
        model = UserSkill
        fields = ('skill', 'proficiency', 'skill_type', 'description', 'experience')
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['skill'].queryset = Skill.objects.all()

class ConnectionRequestForm(forms.ModelForm):
    class Meta:
        model = ConnectionRequest
        fields = ('message',)

class SessionForm(forms.ModelForm):
    class Meta:
        model = Session
        fields = ['skill', 'topic', 'description', 'scheduled_time', 'duration', 'is_online', 'meeting_link', 'location']
        widgets = {
            'scheduled_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'duration': forms.TextInput(attrs={'placeholder': 'e.g., 1:00:00 for 1 hour'}),
            'description': forms.Textarea(attrs={'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['skill'].queryset = Skill.objects.all()
        self.fields['skill'].required = True

class AvailabilityForm(forms.ModelForm):
    class Meta:
        model = Availability
        fields = ('day_of_week', 'start_time', 'end_time')
        widgets = {
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['content']
        widgets = {
            'content': forms.TextInput(attrs={
                'class': 'chat-input-field',
                'placeholder': 'Type a message...',
            })
        }
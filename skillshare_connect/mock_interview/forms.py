#mock_interview\forms.py
from django import forms

SKILL_CHOICES = [
    ('python', 'Python Programming'),
    ('javascript', 'JavaScript'),
    ('data_structures', 'Data Structures'),
    ('machine_learning', 'Machine Learning'),
    ('web_development', 'Web Development'),
]

class StartSessionForm(forms.Form):
    skill = forms.ChoiceField(choices=SKILL_CHOICES, label="Choose skill")

class AnswerForm(forms.Form):
    answer = forms.CharField(widget=forms.Textarea(attrs={'rows':4}), label="Your answer")

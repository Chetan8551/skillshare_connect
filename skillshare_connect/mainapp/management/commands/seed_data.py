from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from mainapp.models import Skill, UserSkill, Availability
import random

class Command(BaseCommand):
    help = 'Seeds the database with sample data'

    def handle(self, *args, **options):
        User = get_user_model()
        
        # Create some skills
        skills_data = [
            {'name': 'Python', 'category': 'Technical'},
            {'name': 'JavaScript', 'category': 'Technical'},
            {'name': 'Web Development', 'category': 'Technical'},
            {'name': 'Data Structures', 'category': 'Technical'},
            {'name': 'Machine Learning', 'category': 'Technical'},
            {'name': 'Graphic Design', 'category': 'Creative'},
            {'name': 'Photography', 'category': 'Creative'},
            {'name': 'Guitar', 'category': 'Creative'},
            {'name': 'Spanish', 'category': 'Language'},
            {'name': 'French', 'category': 'Language'},
        ]
        
        for skill_data in skills_data:
            Skill.objects.get_or_create(**skill_data)
        
        self.stdout.write(self.style.SUCCESS('Successfully seeded skills'))
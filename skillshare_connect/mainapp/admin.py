# D:\Chetan\skill\skillshare_connect\mainapp\admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from mainapp.models import CustomUser, Skill, UserSkill, ConnectionRequest, Session, Review, Availability, Message

# ✅ CustomUser admin registration
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['username', 'email', 'university', 'year_of_study', 'is_staff']
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('university', 'year_of_study', 'bio', 'avatar')}),  # Add your custom fields
    )
    search_fields = ['username', 'email', 'university']
    list_filter = ['year_of_study', 'university', 'is_staff', 'is_superuser']


# ✅ Session admin configuration
@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('topic', 'teacher', 'student', 'scheduled_time', 'status')
    list_filter = ('status', 'scheduled_time', 'teacher')
    search_fields = ('topic', 'teacher__username', 'student__username')
    ordering = ('-scheduled_time',)


# ✅ Register other models
admin.site.register(Skill)
admin.site.register(UserSkill)
admin.site.register(ConnectionRequest)
admin.site.register(Review)
admin.site.register(Availability)
admin.site.register(Message)

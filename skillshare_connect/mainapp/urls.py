from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include

urlpatterns = [
    path('', views.home, name='home'),
    path('search/', views.search_profiles, name='search_profiles'), 
    path('search/', views.search_profiles, name='search'),
    path('profile/', views.profile, name='profile'),  # Current user's profile
    path('profile/<int:user_id>/', views.profile, name='profile_view'),  # Other user's profile
    path('dashboard/', views.dashboard, name='dashboard'),
    path('matches/', views.matches, name='matches'),
    path('auth/', views.auth_view, name='auth'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('add-skill/', views.add_skill, name='add_skill'),
    path('connect/<int:user_id>/', views.send_connection_request, name='send_connection_request'),
    path('connection/<int:request_id>/<str:response>/', views.respond_to_connection_request, name='respond_connection_request'),
    path('schedule/<int:user_id>/', views.schedule_session, name='schedule_session'),
    path('search/', views.search_users, name='search'),
    path('api/matches/', views.api_user_matches, name='api_matches'),
    path('logout/', views.logout_view, name='logout'),
    path('messages/', views.messages_view, name='messages'),
    path('messages/<int:connection_id>/', views.messages_view, name='messages'),
    path('video-call/<int:user_id>/', views.start_video_call, name='video_call'),
    path('session/<int:session_id>/', views.session_detail, name='session_detail'),
    path('session/<int:session_id>/review/', views.add_review, name='add_review'),
    path("profile/<int:user_id>/", views.profile, name="profile"),
    path("connect/<int:user_id>/", views.send_connection_request, name="send_connection_request"),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('reset-password/', views.reset_password, name='reset_password'),
   



]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
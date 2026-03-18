from django.urls import path
from . import views

app_name = "study_sessions"

urlpatterns = [
    path("upcoming/", views.UpcomingSessionsList.as_view(), name="upcoming_sessions"),
    path("<int:pk>/", views.SessionDetail.as_view(), name="session_detail"),
    path("create/", views.CreateSession.as_view(), name="create_session"),
    path("<int:pk>/cancel/", views.cancel_session, name="cancel_session"),
]

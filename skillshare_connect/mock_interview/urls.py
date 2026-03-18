from django.urls import path
from . import views

urlpatterns = [
    path('', views.start_interview, name='start_page'),
    path('dynamic/start/', views.start_dynamic_interview, name='start_dynamic_interview'),
    path('dynamic/answer/', views.answer_dynamic_question, name='answer_dynamic_question'),
]

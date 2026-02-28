from django.urls import path
from . import views

urlpatterns = [
    path('', views.chat_sse, name='chat-sse'),
    path('sessions/', views.chat_sessions, name='chat-sessions'),
]

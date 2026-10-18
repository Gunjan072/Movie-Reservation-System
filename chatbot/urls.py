from django.urls import path
from . import views

app_name = 'chatbot'

urlpatterns = [
    path('api/message/', views.chatbot_message_api, name='chatbot_message'),
]

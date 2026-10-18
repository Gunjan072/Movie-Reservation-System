from django.urls import path
from . import views

app_name = 'recommendations'

urlpatterns = [
    path('', views.recommended_view, name='recommended'),
    path('api/', views.recommendations_api, name='recommendations_api'),
]

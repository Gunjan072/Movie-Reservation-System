from django.urls import path
from . import views

app_name = 'reviews'

urlpatterns = [
    path('add/<int:movie_id>/', views.add_review_view, name='add_review'),
]

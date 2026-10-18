from django.urls import path
from . import views

app_name = 'shows'

urlpatterns = [
    path('<int:show_id>/seats/', views.seat_layout_view, name='seat_layout'),
    path('api/lock-seats/', views.lock_seats_api, name='lock_seats_api'),
]

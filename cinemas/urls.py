from django.urls import path
from . import views

app_name = 'cinemas'

urlpatterns = [
    path('', views.cinema_list_view, name='cinema_list'),
    path('<slug:slug>/', views.cinema_detail_view, name='cinema_detail'),
]

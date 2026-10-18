from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('admin/', views.admin_dashboard_view, name='admin_dashboard'),
    path('manager/', views.manager_dashboard_view, name='manager_dashboard'),
]

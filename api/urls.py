from django.urls import path
from . import views

urlpatterns = [
    path('auth/register/', views.RegisterAPIView.as_view(), name='api-register'),
    path('auth/login/', views.LoginAPIView.as_view(), name='api-login'),
    path('movies/', views.MovieListAPIView.as_view(), name='api-movies'),
    path('movies/<int:pk>/', views.MovieDetailAPIView.as_view(), name='api-movie-detail'),
    path('cinemas/', views.CinemaListAPIView.as_view(), name='api-cinemas'),
    path('cinemas/<int:pk>/', views.CinemaDetailAPIView.as_view(), name='api-cinema-detail'),
    path('shows/', views.ShowListAPIView.as_view(), name='api-shows'),
    path('shows/<int:pk>/seats/', views.ShowSeatsAPIView.as_view(), name='api-show-seats'),
    path('bookings/', views.MyBookingsAPIView.as_view(), name='api-bookings'),
    path('coupons/', views.CouponListAPIView.as_view(), name='api-coupons'),
    path('reviews/', views.ReviewListCreateAPIView.as_view(), name='api-reviews'),
    path('recommendations/', views.recommendations_api, name='api-recommendations'),
]

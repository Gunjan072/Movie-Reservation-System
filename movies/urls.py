from django.urls import path
from . import views

app_name = 'movies'

urlpatterns = [
    path('', views.movie_list_view, name='movie_list'),
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('wishlist/toggle/<int:movie_id>/', views.toggle_wishlist, name='toggle_wishlist'),
    path('api/search/', views.search_suggest_view, name='search_suggest'),
    path('<slug:slug>/', views.movie_detail_view, name='movie_detail'),
]

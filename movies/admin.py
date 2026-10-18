from django.contrib import admin
from .models import Genre, Actor, Movie, Wishlist


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


@admin.register(Actor)
class ActorAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ('title', 'language', 'duration', 'certification', 'rating', 'status', 'is_featured', 'release_date')
    list_filter = ('status', 'certification', 'language', 'is_featured', 'genres')
    search_fields = ('title', 'director', 'synopsis')
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ('genres', 'cast')


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'movie', 'added_at')
    search_fields = ('user__username', 'movie__title')

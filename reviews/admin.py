from django.contrib import admin
from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'movie', 'rating', 'headline', 'is_verified_buyer', 'created_at')
    list_filter = ('rating', 'is_verified_buyer', 'created_at')
    search_fields = ('user__username', 'movie__title', 'headline', 'comment')

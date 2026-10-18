from django.contrib import admin
from .models import ChatMessage


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('user', 'intent', 'user_query', 'created_at')
    list_filter = ('intent', 'created_at')
    search_fields = ('user_query', 'bot_response', 'user__username')

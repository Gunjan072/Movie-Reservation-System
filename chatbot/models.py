from django.db import models
from django.conf import settings


class ChatMessage(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    session_key = models.CharField(max_length=64, blank=True)
    user_query = models.TextField()
    bot_response = models.TextField()
    intent = models.CharField(max_length=50, blank=True, default='general')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Chat ({self.intent}): {self.user_query[:30]}"

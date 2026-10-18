from django.contrib import admin
from .models import Ticket


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('booking', 'verification_code', 'is_verified', 'verified_at', 'created_at')
    list_filter = ('is_verified', 'created_at')
    search_fields = ('booking__booking_id', 'verification_code')
    readonly_fields = ('verification_code', 'created_at')

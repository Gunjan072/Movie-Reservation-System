from django.contrib import admin
from .models import Cinema, Screen, Seat


class ScreenInline(admin.TabularInline):
    model = Screen
    extra = 1


@admin.register(Cinema)
class CinemaAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'state', 'contact_number', 'manager', 'is_active')
    list_filter = ('city', 'is_active')
    search_fields = ('name', 'city', 'address')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ScreenInline]


class SeatInline(admin.TabularInline):
    model = Seat
    extra = 0
    can_delete = True


@admin.register(Screen)
class ScreenAdmin(admin.ModelAdmin):
    list_display = ('name', 'cinema', 'screen_type', 'total_rows', 'seats_per_row', 'total_capacity', 'is_active')
    list_filter = ('screen_type', 'cinema', 'is_active')
    search_fields = ('name', 'cinema__name')
    inlines = [SeatInline]


@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = ('screen', 'row', 'number', 'seat_type', 'price_multiplier', 'is_active')
    list_filter = ('seat_type', 'screen__cinema', 'screen', 'is_active')
    search_fields = ('row', 'screen__name', 'screen__cinema__name')

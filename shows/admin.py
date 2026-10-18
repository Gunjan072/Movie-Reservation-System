from django.contrib import admin
from .models import Show, ShowSeat


class ShowSeatInline(admin.TabularInline):
    model = ShowSeat
    extra = 0
    fields = ('seat', 'price', 'status', 'locked_by', 'locked_until')
    readonly_fields = ('seat', 'price')
    can_delete = False


@admin.register(Show)
class ShowAdmin(admin.ModelAdmin):
    list_display = ('movie', 'get_cinema', 'screen', 'date', 'start_time', 'end_time', 'format', 'base_price', 'is_active')
    list_filter = ('date', 'format', 'screen__cinema', 'movie', 'is_active')
    search_fields = ('movie__title', 'screen__cinema__name', 'screen__name')
    date_hierarchy = 'date'
    inlines = [ShowSeatInline]

    def get_cinema(self, obj):
        return obj.screen.cinema.name
    get_cinema.short_description = 'Cinema'


@admin.register(ShowSeat)
class ShowSeatAdmin(admin.ModelAdmin):
    list_display = ('show', 'seat', 'price', 'status', 'locked_by', 'locked_until')
    list_filter = ('status', 'show__date', 'show__movie')
    search_fields = ('show__movie__title', 'seat__row', 'locked_by__username')

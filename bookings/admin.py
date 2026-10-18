from django.contrib import admin
from .models import Coupon, CouponUsage, Booking, BookingSeat, Refund


class BookingSeatInline(admin.TabularInline):
    model = BookingSeat
    extra = 0
    readonly_fields = ('show_seat', 'seat_price')
    can_delete = False


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_type', 'discount_value', 'min_amount', 'max_discount', 'times_used', 'usage_limit', 'is_active')
    list_filter = ('discount_type', 'is_active')
    search_fields = ('code',)


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('booking_id', 'user', 'get_movie', 'get_cinema', 'final_amount', 'booking_status', 'created_at')
    list_filter = ('booking_status', 'created_at')
    search_fields = ('booking_id', 'user__username', 'show__movie__title')
    readonly_fields = ('booking_id', 'created_at', 'updated_at')
    inlines = [BookingSeatInline]

    def get_movie(self, obj):
        return obj.show.movie.title
    get_movie.short_description = 'Movie'

    def get_cinema(self, obj):
        return obj.show.screen.cinema.name
    get_cinema.short_description = 'Cinema'


@admin.register(CouponUsage)
class CouponUsageAdmin(admin.ModelAdmin):
    list_display = ('coupon', 'user', 'booking', 'used_at')
    search_fields = ('coupon__code', 'user__username', 'booking__booking_id')


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ('booking', 'refund_amount', 'refund_percentage', 'status', 'processed_at')
    list_filter = ('status', 'refund_percentage')
    search_fields = ('booking__booking_id', 'cancellation_reason')

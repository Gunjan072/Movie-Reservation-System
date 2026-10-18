import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


class Coupon(models.Model):
    TYPE_PERCENTAGE = 'PERCENTAGE'
    TYPE_FLAT = 'FLAT'

    DISCOUNT_TYPES = [
        (TYPE_PERCENTAGE, 'Percentage (%)'),
        (TYPE_FLAT, 'Flat Amount (₹)'),
    ]

    code = models.CharField(max_length=50, unique=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES, default=TYPE_FLAT)
    discount_value = models.DecimalField(max_digits=7, decimal_places=2)
    min_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    max_discount = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    valid_from = models.DateTimeField(default=timezone.now)
    valid_until = models.DateTimeField()
    usage_limit = models.PositiveIntegerField(default=100)
    times_used = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def is_valid(self, amount):
        now = timezone.now()
        if not self.is_active:
            return False, "This coupon is no longer active."
        if now < self.valid_from or now > self.valid_until:
            return False, "This coupon has expired."
        if self.times_used >= self.usage_limit:
            return False, "This coupon usage limit has been reached."
        if amount < self.min_amount:
            return False, f"Minimum booking amount of ₹{self.min_amount} required to use this coupon."
        return True, "Coupon is valid."

    def calculate_discount(self, amount):
        valid, msg = self.is_valid(amount)
        if not valid:
            return 0.00
        if self.discount_type == self.TYPE_PERCENTAGE:
            discount = (amount * self.discount_value) / 100
            if self.max_discount and discount > self.max_discount:
                discount = self.max_discount
            return round(discount, 2)
        else:
            return min(self.discount_value, amount)

    def __str__(self):
        return f"{self.code} ({self.get_discount_type_display()} - {self.discount_value})"


class Booking(models.Model):
    STATUS_PENDING = 'PENDING'
    STATUS_CONFIRMED = 'CONFIRMED'
    STATUS_CANCELLED = 'CANCELLED'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending Payment'),
        (STATUS_CONFIRMED, 'Confirmed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    booking_id = models.CharField(max_length=50, unique=True, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookings')
    show = models.ForeignKey('shows.Show', on_delete=models.PROTECT, related_name='bookings')
    total_ticket_price = models.DecimalField(max_digits=10, decimal_places=2)
    convenience_fee = models.DecimalField(max_digits=7, decimal_places=2, default=30.00)
    tax_amount = models.DecimalField(max_digits=7, decimal_places=2, default=0.00)
    discount_amount = models.DecimalField(max_digits=7, decimal_places=2, default=0.00)
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True, related_name='bookings')
    final_amount = models.DecimalField(max_digits=10, decimal_places=2)
    booking_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.booking_id:
            short_id = uuid.uuid4().hex[:8].upper()
            date_str = timezone.now().strftime('%Y%m%d')
            self.booking_id = f"CR-{date_str}-{short_id}"
        super().save(*args, **kwargs)

    @property
    def seat_labels(self):
        return ", ".join([bs.show_seat.seat.label for bs in self.booked_seats.select_related('show_seat__seat')])

    @property
    def can_cancel(self):
        if self.booking_status != self.STATUS_CONFIRMED:
            return False
        # Check time before show start
        show_datetime = timezone.make_aware(
            timezone.datetime.combine(self.show.date, self.show.start_time)
        )
        return timezone.now() < show_datetime

    def refund_percentage_eligibility(self):
        show_datetime = timezone.make_aware(
            timezone.datetime.combine(self.show.date, self.show.start_time)
        )
        hours_before = (show_datetime - timezone.now()).total_seconds() / 3600.0
        if hours_before > 24:
            return 100
        elif 2 <= hours_before <= 24:
            return 75
        else:
            return 0

    def __str__(self):
        return f"{self.booking_id} - {self.user.username} ({self.get_booking_status_display()})"


class BookingSeat(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='booked_seats')
    show_seat = models.ForeignKey('shows.ShowSeat', on_delete=models.PROTECT)
    seat_price = models.DecimalField(max_digits=7, decimal_places=2)

    def __str__(self):
        return f"{self.booking.booking_id} - Seat {self.show_seat.seat.label}"


class CouponUsage(models.Model):
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name='usages')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='coupon_usages')
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='coupon_usages')
    used_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('coupon', 'booking')

    def __str__(self):
        return f"{self.coupon.code} used by {self.user.username} on {self.booking.booking_id}"


class Refund(models.Model):
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='refund')
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2)
    refund_percentage = models.PositiveIntegerField(help_text="100, 75, or 0 percent")
    cancellation_reason = models.TextField(blank=True, default='')
    processed_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='PROCESSED')

    def __str__(self):
        return f"Refund for {self.booking.booking_id}: ₹{self.refund_amount} ({self.refund_percentage}%)"

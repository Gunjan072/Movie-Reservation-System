from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings
from movies.models import Movie
from cinemas.models import Screen, Seat


class Show(models.Model):
    FORMAT_2D = '2D'
    FORMAT_3D = '3D'
    FORMAT_IMAX = 'IMAX'
    FORMAT_4DX = '4DX'

    FORMAT_CHOICES = [
        (FORMAT_2D, '2D'),
        (FORMAT_3D, '3D'),
        (FORMAT_IMAX, 'IMAX'),
        (FORMAT_4DX, '4DX'),
    ]

    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='shows')
    screen = models.ForeignKey(Screen, on_delete=models.CASCADE, related_name='shows')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    format = models.CharField(max_length=10, choices=FORMAT_CHOICES, default=FORMAT_2D)
    language = models.CharField(max_length=50, default='English')
    base_price = models.DecimalField(max_digits=7, decimal_places=2, default=250.00)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['date', 'start_time']

    def clean(self):
        super().clean()
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError({'end_time': "End time must be after start time."})

        # Overlapping show collision detection on the same screen and date
        if self.screen_id and self.date and self.start_time and self.end_time:
            overlapping = Show.objects.filter(
                screen=self.screen,
                date=self.date,
                is_active=True
            ).exclude(pk=self.pk)

            # Check overlap: (StartA < EndB) and (EndA > StartB)
            for show in overlapping:
                if (self.start_time < show.end_time) and (self.end_time > show.start_time):
                    raise ValidationError(
                        f"Screen conflict: Another show '{show.movie.title}' is already scheduled from "
                        f"{show.start_time.strftime('%I:%M %p')} to {show.end_time.strftime('%I:%M %p')} on this screen."
                    )

    def save(self, *args, **kwargs):
        self.clean()
        is_new = self.pk is None
        super().save(*args, **kwargs)

        # Automatically populate ShowSeat instances for this screen's seats
        if is_new:
            self.generate_show_seats()

    def generate_show_seats(self):
        from decimal import Decimal
        seats = Seat.objects.filter(screen=self.screen, is_active=True)
        show_seats = []
        for seat in seats:
            calculated_price = round(Decimal(str(self.base_price)) * Decimal(str(seat.price_multiplier)), 2)
            show_seats.append(
                ShowSeat(
                    show=self,
                    seat=seat,
                    price=calculated_price,
                    status=ShowSeat.STATUS_AVAILABLE
                )
            )
        ShowSeat.objects.bulk_create(show_seats, ignore_conflicts=True)

    @property
    def cinema(self):
        return self.screen.cinema

    def available_seats_count(self):
        now = timezone.now()
        # Seats are available if status is AVAILABLE, or if status is LOCKED but lock expired
        count = self.show_seats.filter(
            models.Q(status=ShowSeat.STATUS_AVAILABLE) |
            (models.Q(status=ShowSeat.STATUS_LOCKED) & models.Q(locked_until__lte=now))
        ).count()
        return count

    def __str__(self):
        return f"{self.movie.title} - {self.screen.cinema.name} ({self.date} {self.start_time.strftime('%I:%M %p')})"


class ShowSeat(models.Model):
    STATUS_AVAILABLE = 'AVAILABLE'
    STATUS_LOCKED = 'LOCKED'
    STATUS_BOOKED = 'BOOKED'

    STATUS_CHOICES = [
        (STATUS_AVAILABLE, 'Available'),
        (STATUS_LOCKED, 'Temporarily Locked'),
        (STATUS_BOOKED, 'Booked'),
    ]

    show = models.ForeignKey(Show, on_delete=models.CASCADE, related_name='show_seats')
    seat = models.ForeignKey(Seat, on_delete=models.CASCADE, related_name='show_seats')
    price = models.DecimalField(max_digits=7, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_AVAILABLE)
    locked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='locked_seats'
    )
    locked_until = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('show', 'seat')
        ordering = ['seat__row', 'seat__number']

    def is_available(self):
        if self.status == self.STATUS_AVAILABLE:
            return True
        if self.status == self.STATUS_LOCKED:
            if self.locked_until and self.locked_until <= timezone.now():
                return True
        return False

    def is_locked_by_user(self, user):
        if self.status == self.STATUS_LOCKED and self.locked_by == user:
            if self.locked_until and self.locked_until > timezone.now():
                return True
        return False

    def __str__(self):
        return f"{self.show.movie.title} | {self.seat.label} ({self.status})"

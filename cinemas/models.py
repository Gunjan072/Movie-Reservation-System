from django.db import models
from django.utils.text import slugify
from django.conf import settings


class Cinema(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=250, unique=True, blank=True)
    address = models.CharField(max_length=300)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, default='Maharashtra')
    postal_code = models.CharField(max_length=20, default='400001')
    contact_number = models.CharField(max_length=20)
    email = models.EmailField(blank=True, default='')
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_cinemas'
    )
    facilities = models.TextField(
        help_text="Comma-separated amenities e.g. Parking, Food Court, Dolby Atmos, Wheelchair Access",
        default="Parking, Food Court, Dolby Atmos, Wheelchair Access"
    )
    image = models.ImageField(upload_to='cinemas/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['city', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.name}-{self.city}")
        super().save(*args, **kwargs)

    @property
    def facilities_list(self):
        return [f.strip() for f in self.facilities.split(',') if f.strip()]

    def __str__(self):
        return f"{self.name} ({self.city})"


class Screen(models.Model):
    TYPE_2D = '2D'
    TYPE_3D = '3D'
    TYPE_IMAX = 'IMAX'
    TYPE_4DX = '4DX'

    SCREEN_TYPES = [
        (TYPE_2D, 'Standard 2D'),
        (TYPE_3D, 'Digital 3D'),
        (TYPE_IMAX, 'IMAX with Laser'),
        (TYPE_4DX, '4DX Motion'),
    ]

    cinema = models.ForeignKey(Cinema, on_delete=models.CASCADE, related_name='screens')
    name = models.CharField(max_length=100)
    screen_type = models.CharField(max_length=20, choices=SCREEN_TYPES, default=TYPE_2D)
    total_rows = models.PositiveIntegerField(default=7)  # A to G
    seats_per_row = models.PositiveIntegerField(default=10) # 1 to 10
    total_capacity = models.PositiveIntegerField(default=70)
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        self.total_capacity = self.total_rows * self.seats_per_row
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.cinema.name} - {self.name} ({self.screen_type})"


class Seat(models.Model):
    TYPE_REGULAR = 'REGULAR'
    TYPE_PREMIUM = 'PREMIUM'
    TYPE_VIP = 'VIP'
    TYPE_RECLINER = 'RECLINER'

    SEAT_TYPES = [
        (TYPE_REGULAR, 'Regular'),
        (TYPE_PREMIUM, 'Premium'),
        (TYPE_VIP, 'VIP Club'),
        (TYPE_RECLINER, 'Luxury Recliner'),
    ]

    screen = models.ForeignKey(Screen, on_delete=models.CASCADE, related_name='seats')
    row = models.CharField(max_length=5)  # e.g., 'A', 'B'
    number = models.PositiveIntegerField() # e.g., 1, 2
    seat_type = models.CharField(max_length=20, choices=SEAT_TYPES, default=TYPE_REGULAR)
    price_multiplier = models.DecimalField(max_digits=4, decimal_places=2, default=1.00)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('screen', 'row', 'number')
        ordering = ['row', 'number']

    @property
    def label(self):
        return f"{self.row}{self.number}"

    def __str__(self):
        return f"{self.screen} - Seat {self.label} ({self.get_seat_type_display()})"

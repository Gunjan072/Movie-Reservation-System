from django.db import models
from django.utils.text import slugify
from django.conf import settings


class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True, default='')

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Actor(models.Model):
    name = models.CharField(max_length=150)
    biography = models.TextField(blank=True, default='')
    photo = models.ImageField(upload_to='actors/', blank=True, null=True)

    def __str__(self):
        return self.name


class Movie(models.Model):
    STATUS_NOW_SHOWING = 'NOW_SHOWING'
    STATUS_COMING_SOON = 'COMING_SOON'
    STATUS_ARCHIVED = 'ARCHIVED'

    STATUS_CHOICES = [
        (STATUS_NOW_SHOWING, 'Now Showing'),
        (STATUS_COMING_SOON, 'Coming Soon'),
        (STATUS_ARCHIVED, 'Archived'),
    ]

    CERT_U = 'U'
    CERT_UA = 'UA'
    CERT_A = 'A'
    CERT_R = 'R'
    CERT_PG13 = 'PG-13'

    CERTIFICATION_CHOICES = [
        (CERT_U, 'U (Universal)'),
        (CERT_UA, 'UA (Parental Guidance)'),
        (CERT_A, 'A (Adults Only)'),
        (CERT_R, 'R (Restricted)'),
        (CERT_PG13, 'PG-13'),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=250, unique=True, blank=True)
    synopsis = models.TextField()
    duration = models.PositiveIntegerField(help_text="Duration in minutes")
    genres = models.ManyToManyField(Genre, related_name='movies')
    language = models.CharField(max_length=50, default='English')
    release_date = models.DateField()
    director = models.CharField(max_length=150)
    cast = models.ManyToManyField(Actor, related_name='movies', blank=True)
    certification = models.CharField(max_length=10, choices=CERTIFICATION_CHOICES, default=CERT_UA)
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=8.0)
    votes_count = models.PositiveIntegerField(default=0)
    poster = models.ImageField(upload_to='posters/', blank=True, null=True)
    banner_image = models.ImageField(upload_to='posters/banners/', blank=True, null=True)
    trailer_url = models.URLField(blank=True, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_NOW_SHOWING)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-release_date', 'title']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    @property
    def formatted_duration(self):
        hours = self.duration // 60
        mins = self.duration % 60
        return f"{hours}h {mins}m"

    def __str__(self):
        return self.title


class Wishlist(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wishlist_items')
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='wished_by')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'movie')
        ordering = ['-added_at']

    def __str__(self):
        return f"{self.user.username} - {self.movie.title}"

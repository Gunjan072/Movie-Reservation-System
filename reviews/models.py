from django.db import models
from django.conf import settings
from django.db.models import Avg


class Review(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews')
    movie = models.ForeignKey('movies.Movie', on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField(choices=[(i, str(i)) for i in range(1, 6)], default=5)
    headline = models.CharField(max_length=150)
    comment = models.TextField()
    is_verified_buyer = models.BooleanField(default=False, help_text="User had a confirmed booking for this movie")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'movie')
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        # Auto-check if user is a verified buyer
        from bookings.models import Booking
        if not self.is_verified_buyer:
            has_booked = Booking.objects.filter(
                user=self.user,
                show__movie=self.movie,
                booking_status=Booking.STATUS_CONFIRMED
            ).exists()
            self.is_verified_buyer = has_booked

        super().save(*args, **kwargs)
        self.update_movie_rating()

    def update_movie_rating(self):
        agg = Review.objects.filter(movie=self.movie).aggregate(avg_rating=Avg('rating'), count=models.Count('id'))
        if agg['avg_rating'] is not None:
            self.movie.rating = round(agg['avg_rating'] * 2, 1)  # Convert 5-star scale to 10-scale IMDb style
            self.movie.votes_count = agg['count']
            self.movie.save(update_fields=['rating', 'votes_count'])

    def __str__(self):
        return f"{self.user.username} on {self.movie.title} - {self.rating} Stars"

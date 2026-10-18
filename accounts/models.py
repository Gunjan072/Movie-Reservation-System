from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver


class User(AbstractUser):
    ROLE_CUSTOMER = 'CUSTOMER'
    ROLE_ADMIN = 'ADMIN'
    ROLE_CINEMA_MANAGER = 'CINEMA_MANAGER'

    ROLE_CHOICES = [
        (ROLE_CUSTOMER, 'Customer'),
        (ROLE_ADMIN, 'System Administrator'),
        (ROLE_CINEMA_MANAGER, 'Cinema Manager'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_CUSTOMER)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='avatars/', blank=True, null=True)

    @property
    def is_customer(self):
        return self.role == self.ROLE_CUSTOMER

    @property
    def is_admin_user(self):
        return self.role == self.ROLE_ADMIN or self.is_superuser

    @property
    def is_cinema_manager(self):
        return self.role == self.ROLE_CINEMA_MANAGER

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    preferred_language = models.CharField(max_length=50, default='English')
    favorite_genre = models.CharField(max_length=50, blank=True, default='')
    loyalty_points = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile: {self.user.username}"


class Notification(models.Model):
    TYPE_INFO = 'INFO'
    TYPE_SUCCESS = 'SUCCESS'
    TYPE_WARNING = 'WARNING'
    TYPE_TICKET = 'TICKET'

    TYPE_CHOICES = [
        (TYPE_INFO, 'Information'),
        (TYPE_SUCCESS, 'Success'),
        (TYPE_WARNING, 'Warning'),
        (TYPE_TICKET, 'Ticket Notification'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_INFO)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.user.username}: {self.title}"


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    else:
        if hasattr(instance, 'profile'):
            instance.profile.save()

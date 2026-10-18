import uuid
from django.db import models


class Payment(models.Model):
    METHOD_UPI = 'UPI'
    METHOD_CARD = 'CARD'
    METHOD_NETBANKING = 'NETBANKING'
    METHOD_WALLET = 'WALLET'

    METHOD_CHOICES = [
        (METHOD_UPI, 'UPI (Google Pay, PhonePe, Paytm)'),
        (METHOD_CARD, 'Credit / Debit Card'),
        (METHOD_NETBANKING, 'Net Banking'),
        (METHOD_WALLET, 'Digital Wallet'),
    ]

    STATUS_SUCCESS = 'SUCCESS'
    STATUS_FAILED = 'FAILED'
    STATUS_REFUNDED = 'REFUNDED'

    STATUS_CHOICES = [
        (STATUS_SUCCESS, 'Success'),
        (STATUS_FAILED, 'Failed'),
        (STATUS_REFUNDED, 'Refunded'),
    ]

    booking = models.OneToOneField('bookings.Booking', on_delete=models.CASCADE, related_name='payment')
    transaction_id = models.CharField(max_length=100, unique=True, editable=False)
    payment_method = models.CharField(max_length=20, choices=METHOD_CHOICES, default=METHOD_UPI)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_SUCCESS)
    gateway_order_id = models.CharField(max_length=100, blank=True, default='')
    gateway_payment_id = models.CharField(max_length=100, blank=True, default='')
    gateway_signature = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.transaction_id:
            self.transaction_id = f"TXN-{uuid.uuid4().hex[:12].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.transaction_id} - ₹{self.amount} ({self.get_status_display()})"

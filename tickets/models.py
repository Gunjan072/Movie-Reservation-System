import io
import uuid
import qrcode
from django.db import models
from django.core.files.base import ContentFile


class Ticket(models.Model):
    booking = models.OneToOneField('bookings.Booking', on_delete=models.CASCADE, related_name='ticket')
    verification_code = models.CharField(max_length=64, unique=True, editable=False)
    qr_code = models.ImageField(upload_to='qrcodes/', blank=True, null=True)
    pdf_ticket = models.FileField(upload_to='tickets_pdf/', blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.verification_code:
            self.verification_code = uuid.uuid4().hex.upper()
        
        super().save(*args, **kwargs)

        if not self.qr_code:
            self.generate_qr()

    def generate_qr(self):
        qr_data = (
            f"CINERESERVE-TICKET\n"
            f"Booking: {self.booking.booking_id}\n"
            f"Movie: {self.booking.show.movie.title}\n"
            f"Cinema: {self.booking.show.screen.cinema.name}\n"
            f"Screen: {self.booking.show.screen.name}\n"
            f"Seats: {self.booking.seat_labels}\n"
            f"Date: {self.booking.show.date}\n"
            f"Time: {self.booking.show.start_time.strftime('%I:%M %p')}\n"
            f"Verify: {self.verification_code}"
        )
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=8,
            border=2,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#0F172A", back_color="#FFFFFF")

        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        file_name = f"qr_{self.booking.booking_id}.png"
        self.qr_code.save(file_name, ContentFile(buffer.getvalue()), save=False)
        super().save(update_fields=['qr_code'])

    def __str__(self):
        return f"Ticket for {self.booking.booking_id} (Code: {self.verification_code[:8]})"

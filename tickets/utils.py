import io
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from django.core.files.base import ContentFile


def generate_ticket_pdf_bytes(ticket):
    """
    Generates a professional cinema ticket PDF using ReportLab.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=(400, 600),
        rightMargin=20,
        leftMargin=20,
        topMargin=20,
        bottomMargin=20
    )

    story = []
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#E50914'),
        alignment=1  # Center
    )

    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontSize=10,
        leading=12,
        textColor=colors.HexColor('#64748B'),
        alignment=1
    )

    movie_title_style = ParagraphStyle(
        'MovieTitle',
        parent=styles['Heading2'],
        fontSize=16,
        leading=20,
        textColor=colors.HexColor('#0F172A'),
        alignment=1
    )

    meta_style = ParagraphStyle(
        'MetaStyle',
        parent=styles['Normal'],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#334155')
    )

    meta_bold = ParagraphStyle(
        'MetaBold',
        parent=styles['Normal'],
        fontSize=9,
        leading=13,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#0F172A')
    )

    # 1. Header Brand
    story.append(Paragraph("CINERESERVE TICKETS", title_style))
    story.append(Paragraph("Official Digital E-Ticket & Entry Pass", subtitle_style))
    story.append(Spacer(1, 15))

    # 2. Movie Name & Format
    booking = ticket.booking
    show = booking.show
    story.append(Paragraph(f"<b>{show.movie.title}</b> ({show.format})", movie_title_style))
    story.append(Paragraph(f"{show.movie.language} • {show.movie.get_certification_display()} • {show.movie.formatted_duration}", subtitle_style))
    story.append(Spacer(1, 15))

    # 3. Ticket Info Table
    data = [
        [Paragraph("Booking ID:", meta_style), Paragraph(f"<b>{booking.booking_id}</b>", meta_bold)],
        [Paragraph("Cinema:", meta_style), Paragraph(f"{show.screen.cinema.name}", meta_bold)],
        [Paragraph("Auditorium:", meta_style), Paragraph(f"{show.screen.name}", meta_bold)],
        [Paragraph("Date & Time:", meta_style), Paragraph(f"{show.date.strftime('%a, %d %b %Y')} at {show.start_time.strftime('%I:%M %p')}", meta_bold)],
        [Paragraph("Reserved Seats:", meta_style), Paragraph(f"<b>{booking.seat_labels}</b>", meta_bold)],
        [Paragraph("Guest Name:", meta_style), Paragraph(f"{booking.user.get_full_name() or booking.user.username}", meta_bold)],
        [Paragraph("Total Amount:", meta_style), Paragraph(f"<b>₹{booking.final_amount}</b> (Paid)", meta_bold)],
        [Paragraph("Status:", meta_style), Paragraph("<b>CONFIRMED</b>", ParagraphStyle('Conf', parent=meta_bold, textColor=colors.HexColor('#16A34A')))],
    ]

    t = Table(data, colWidths=[110, 250])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#E2E8F0')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(t)
    story.append(Spacer(1, 15))

    # 4. QR Code Image
    if ticket.qr_code and hasattr(ticket.qr_code, 'path'):
        try:
            qr_img = RLImage(ticket.qr_code.path, width=120, height=120)
            qr_img.hAlign = 'CENTER'
            story.append(qr_img)
            story.append(Spacer(1, 5))
            story.append(Paragraph(f"Verification Code: {ticket.verification_code[:12]}...", subtitle_style))
        except Exception:
            pass

    story.append(Spacer(1, 15))
    story.append(Paragraph("Please display this digital ticket or QR pass at the cinema turnstile.", subtitle_style))
    story.append(Paragraph("Enjoy your cinematic experience at CineReserve!", subtitle_style))

    doc.build(story)
    pdf_data = buffer.getvalue()
    buffer.close()
    return pdf_data

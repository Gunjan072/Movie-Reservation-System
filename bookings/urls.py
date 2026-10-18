from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    path('summary/', views.booking_summary_view, name='booking_summary'),
    path('apply-coupon/', views.apply_coupon_view, name='apply_coupon'),
    path('remove-coupon/', views.remove_coupon_view, name='remove_coupon'),
    path('release-seats/', views.release_seats_view, name='release_seats'),
    path('payment/', views.payment_gateway_view, name='payment'),
    path('payment/process/', views.process_payment_view, name='process_payment'),
    path('confirmed/<str:booking_id>/', views.booking_success_view, name='booking_success'),
    path('failed/', views.booking_failed_view, name='booking_failed'),
    path('ticket/<str:booking_id>/', views.booking_success_view, name='view_ticket'),
    path('my-bookings/', views.my_bookings_view, name='my_bookings'),
    path('cancel/<str:booking_id>/', views.cancel_booking_view, name='cancel_booking'),
    path('ticket/<str:booking_id>/download-pdf/', views.download_ticket_pdf, name='download_ticket_pdf'),
    path('offers/', views.offers_view, name='offers'),
    path('terms/', views.terms_view, name='terms'),
    path('privacy/', views.privacy_view, name='privacy'),
    path('refund-policy/', views.refund_policy_view, name='refund_policy'),
    path('faq/', views.faq_view, name='faq'),
    path('about/', views.about_view, name='about'),
]

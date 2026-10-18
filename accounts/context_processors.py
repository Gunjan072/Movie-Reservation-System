def notification_context(request):
    """
    Context processor to inject unread notification count for authenticated users.
    """
    if request.user.is_authenticated:
        try:
            from accounts.models import Notification
            unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
            return {'unread_notifications_count': unread_count}
        except Exception:
            return {'unread_notifications_count': 0}
    return {'unread_notifications_count': 0}

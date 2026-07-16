def notifications_processor(request):
    if request.user.is_authenticated:
        unread_notifications = request.user.notifications.filter(is_read=False).order_by('-created_at')[:10]
        unread_count = request.user.notifications.filter(is_read=False).count()
        return {
            'unread_notifications': unread_notifications,
            'unread_notifications_count': unread_count
        }
    return {}

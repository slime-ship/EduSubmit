def notifications_processor(request):
    if request.user.is_authenticated:
        if hasattr(request.user, 'student_profile'):
            try:
                from django.utils import timezone
                from datetime import timedelta
                from .models import Assignment, Submission, Notification
                
                student = request.user.student_profile
                now = timezone.now()
                # Close to deadline is defined as within 48 hours
                close_time = now + timedelta(hours=48)
                
                # Query active assignments due in the near future (within 48 hours)
                upcoming_assignments = Assignment.objects.filter(
                    course__department=student.department,
                    course__level=student.level,
                    course__is_active=True,
                    session__is_active=True,
                    semester__is_active=True,
                    deadline__gt=now,
                    deadline__lte=close_time
                ).select_related('course')
                
                for assignment in upcoming_assignments:
                    # Check if student already submitted this assignment
                    has_submitted = Submission.objects.filter(assignment=assignment, student=student).exists()
                    if not has_submitted:
                        # Check if a notification already exists for this assignment
                        msg_marker = f"'{assignment.title}' ({assignment.course.code}) is approaching"
                        notification_exists = Notification.objects.filter(
                            recipient=request.user,
                            message__contains=msg_marker
                        ).exists()
                        
                        if not notification_exists:
                            deadline_str = assignment.deadline.strftime("%b %d, %Y at %H:%M")
                            Notification.objects.create(
                                recipient=request.user,
                                message=f"Warning: The deadline for '{assignment.title}' ({assignment.course.code}) is approaching. Due on {deadline_str}.",
                                link=f"/student/upload/?assignment_id={assignment.id}"
                            )
            except Exception as e:
                pass
                
        unread_notifications = request.user.notifications.filter(is_read=False).order_by('-created_at')[:10]
        unread_count = request.user.notifications.filter(is_read=False).count()
        return {
            'unread_notifications': unread_notifications,
            'unread_notifications_count': unread_count
        }
    return {}

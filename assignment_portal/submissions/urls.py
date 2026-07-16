from django.urls import path, include
from django.shortcuts import redirect
from django.contrib.auth import views as auth_views
from django.utils.functional import SimpleLazyObject
from django.views.generic import TemplateView
from rest_framework.routers import DefaultRouter
from . import views
from .admin import LecturerAdminSite

urlpatterns = [
    path('manifest.json', TemplateView.as_view(template_name='submissions/manifest.json', content_type='application/json'), name='manifest_json'),
    path('sw.js', TemplateView.as_view(template_name='submissions/sw.js', content_type='application/javascript'), name='sw_js'),
    path('', lambda request: redirect('login')),
    path('register/', views.register, name='register'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('complete_student_profile/', views.complete_student_profile, name='complete_student_profile'),
    path('complete_lecturer_profile/', views.complete_lecturer_profile, name='complete_lecturer_profile'),
    
    # Student URLs
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student/upload/', views.upload_assignment, name='upload_assignment'),
    path('student/assignments/', views.student_assignments, name='student_assignments'),
    path('student/profile/', views.student_profile, name='student_profile'),
    
    # Lecturer URLs
    path('lecturer/dashboard/', views.lecturer_dashboard, name='lecturer_dashboard'),
    path('lecturer/assignments/', views.lecturer_assignments, name='lecturer_assignments'),
    path('lecturer/courses/', views.lecturer_courses, name='lecturer_courses'),
    path('lecturer/grade/<int:assignment_id>/', views.grade_assignment, name='grade_assignment'),
    path('lecturer/students/', views.lecturer_students, name='lecturer_students'),
    path('lecturer/create-assignment/', views.create_assignment, name='create_assignment'),
    path('lecturer/profile/', views.lecturer_profile, name='lecturer_profile'),

    # Global Tools
    path('search/', views.global_search, name='global_search'),
    path('reports/', views.reports_view, name='reports_view'),
    path('notifications/', views.notifications_list, name='notifications_list'),
    path('notifications/read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),



    # Password Reset URLs
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='registration/password_reset_form.html',
             email_template_name='registration/password_reset_email.html',
             subject_template_name='registration/password_reset_subject.txt'
         ), 
         name='password_reset'),
    
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='registration/password_reset_done.html'
         ), 
         name='password_reset_done'),
    
    path('password-reset-confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='registration/password_reset_confirm.html'
         ), 
         name='password_reset_confirm'),
    
    path('password-reset-complete/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='registration/password_reset_complete.html'
         ), 
         name='password_reset_complete'),
]

# REST API Routing
router = DefaultRouter()
router.register('api/students', views.StudentViewSet, basename='api-student')
router.register('api/lecturers', views.LecturerViewSet, basename='api-lecturer')
urlpatterns += [
    path('', include(router.urls)),
]

# Add this at the BOTTOM of your urls.py AFTER successful migrations
import sys

# Only add lecturer URLs if we're not running migrations
if 'makemigrations' not in sys.argv and 'migrate' not in sys.argv:
    try:
        from .models import LecturerProfile
        
        def _get_lecturer_admin_urls():
            """Inner function that queries the database - only called when needed"""
            urls = []
            for lecturer in LecturerProfile.objects.all():
                lecturer_site = LecturerAdminSite(lecturer, name=f'lecturer_{lecturer.staff_id}')
                # Register models on the site
                from .admin import register_lecturer_admin_models
                register_lecturer_admin_models(lecturer_site)
                urls.append(path(f'lecturer/{lecturer.staff_id}/admin/', lecturer_site.urls))
            return urls
        
        # Use SimpleLazyObject to delay execution until first access
        lecturer_urls = SimpleLazyObject(lambda: _get_lecturer_admin_urls())
        urlpatterns += lecturer_urls
    except Exception as e:
        print(f"Warning: Could not create lecturer admin URLs: {e}")
        # Continue without lecturer admin URLs
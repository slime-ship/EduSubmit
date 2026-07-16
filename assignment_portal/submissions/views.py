from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Avg, Count, Q
import csv

from .forms import (
    UserRegistrationForm, StudentProfileForm, StudentProfileEditForm,
    LecturerProfileForm, LecturerProfileEditForm, AssignmentForm, SubmissionForm, GradeAssignmentForm
)
from .models import (
    UserProfile, StudentProfile, LecturerProfile, 
    Assignment, Course, Faculty, Department, Level,
    AcademicSession, Semester, Submission, Grade, Notification
)

# ---------- Utility Functions ----------
def is_student(user):
    return hasattr(user, 'student_profile')

def is_lecturer(user):
    return hasattr(user, 'lecturer_profile')


class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        user = self.request.user
        if hasattr(user, 'student_profile'):
            return '/student/dashboard/'
        elif hasattr(user, 'lecturer_profile'):
            return '/lecturer/dashboard/'
        elif user.is_superuser:
            return '/admin/'
        return '/'
    
    def form_valid(self, form):
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        user = authenticate(self.request, username=username, password=password)
        
        if user is not None:
            login(self.request, user)
            if not self.request.POST.get('remember'):
                self.request.session.set_expiry(0)
            else:
                self.request.session.set_expiry(1209600)  # 2 weeks
            
            messages.success(self.request, f'Welcome back, {user.full_name}!')
            return redirect(self.get_success_url())
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Invalid username or password. Please try again.')
        return super().form_invalid(form)


def register(request):
    if request.user.is_authenticated:
        if hasattr(request.user, 'student_profile'):
            return redirect('student_dashboard')
        elif hasattr(request.user, 'lecturer_profile'):
            return redirect('lecturer_dashboard')
        return redirect('/admin/')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            if user.user_type == 'student':
                request.session['new_user_id'] = user.id
                messages.success(request, 'Student account created! Please complete your profile.')
                return redirect('complete_student_profile')
            elif user.user_type == 'lecturer':
                # Auto-login lecturer and complete profile
                request.session['new_user_id'] = user.id
                messages.success(request, 'Lecturer account created! Please complete your profile.')
                return redirect('complete_lecturer_profile')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = UserRegistrationForm()
    
    return render(request, 'registration/register.html', {'form': form})


def complete_student_profile(request):
    user_id = request.session.get('new_user_id')
    if not user_id:
        return redirect('register')
    
    user = get_object_or_404(UserProfile, id=user_id)
    current_year = timezone.now().year
    years = [str(year) for year in range(current_year, current_year - 6, -1)]
    
    if request.method == 'POST':
        form = StudentProfileForm(request.POST, instance=user.student_profile)
        if form.is_valid():
            form.save()
            del request.session['new_user_id']
            login(request, user)
            messages.success(request, f'Welcome, {user.full_name}! Your profile is complete.')
            return redirect('student_dashboard')
    else:
        form = StudentProfileForm(instance=user.student_profile)
    
    context = {
        'user': user,
        'form': form,
        'faculties': Faculty.objects.all(),
        'departments': Department.objects.all(),
        'levels': Level.objects.all(),
        'years': years,
    }
    return render(request, 'submissions/complete_student_profile.html', context)


def complete_lecturer_profile(request):
    user_id = request.session.get('new_user_id')
    if not user_id:
        return redirect('register')
    
    user = get_object_or_404(UserProfile, id=user_id)
    
    if request.method == 'POST':
        form = LecturerProfileForm(request.POST, instance=user.lecturer_profile)
        if form.is_valid():
            form.save()
            user.is_staff = True
            user.save()
            del request.session['new_user_id']
            login(request, user)
            messages.success(request, f'Welcome, {user.full_name}! Your profile is complete.')
            return redirect('lecturer_dashboard')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = LecturerProfileForm(instance=user.lecturer_profile)
        
    context = {
        'user': user,
        'form': form,
        'faculties': Faculty.objects.all(),
        'departments': Department.objects.all(),
    }
    return render(request, 'submissions/complete_lecturer_profile.html', context)


# ---------- Student Views ----------
@login_required
@user_passes_test(is_student)
def student_dashboard(request):
    student = request.user.student_profile
    
    # Enrolled active courses
    current_courses = Course.objects.filter(
        department=student.department,
        level=student.level,
        is_active=True
    ).select_related('lecturer__user')
    
    # Submissions
    submissions = Submission.objects.filter(
        student=student
    ).select_related('assignment__course', 'grade_record')
    
    total_submissions = submissions.count()
    graded_submissions = submissions.filter(status='graded')
    graded_count = graded_submissions.count()
    pending_count = submissions.filter(status__in=['pending', 'under_review']).count()
    
    # Average Score
    scores = [s.grade_record.score for s in graded_submissions if hasattr(s, 'grade_record') and s.grade_record]
    average_score = round(sum(scores) / len(scores), 1) if scores else 'N/A'
    
    # Completion Rate
    total_assignments_avail = Assignment.objects.filter(
        course__in=current_courses,
        session__is_active=True
    ).count()
    completion_percentage = (total_submissions / total_assignments_avail * 100) if total_assignments_avail > 0 else 0
    
    recent_submissions = submissions.order_by('-date_uploaded')[:5]
    
    context = {
        'student': student,
        'courses': current_courses,
        'total_assignments': total_submissions,
        'graded_assignments': graded_count,
        'pending_assignments': pending_count,
        'total_courses': current_courses.count(),
        'completion_percentage': round(completion_percentage),
        'average_grade': average_score,
        'recent_assignments': recent_submissions,
    }
    return render(request, 'submissions/student_dashboard.html', context)


@login_required
@user_passes_test(is_student)
def upload_assignment(request):
    student = request.user.student_profile
    
    # Get active courses for student
    current_courses = Course.objects.filter(
        department=student.department,
        level=student.level,
        is_active=True
    )
    # Active assignments for those courses
    assignments = Assignment.objects.filter(
        course__in=current_courses,
        session__is_active=True,
        semester__is_active=True
    ).select_related('course')
    
    assignment_id = request.GET.get('assignment_id')
    selected_assignment = None
    if assignment_id:
        selected_assignment = get_object_or_404(Assignment, id=assignment_id, course__in=current_courses)
        
    if request.method == 'POST':
        form = SubmissionForm(request.POST, request.FILES)
        target_assignment_id = request.POST.get('assignment')
        
        target_assignment = get_object_or_404(Assignment, id=target_assignment_id, course__in=current_courses)
        
        if form.is_valid():
            submission, created = Submission.objects.get_or_create(
                assignment=target_assignment,
                student=student,
                defaults={'file': form.cleaned_data['file']}
            )
            if not created:
                submission.file = form.cleaned_data['file']
                submission.status = 'pending'
                submission.save()
                
            # Create notification for lecturer
            if target_assignment.course.lecturer:
                Notification.objects.create(
                    recipient=target_assignment.course.lecturer.user,
                    sender=request.user,
                    message=f'New assignment upload: "{target_assignment.title}" by {student.user.full_name}.',
                    link='/lecturer/assignments/'
                )
                
            messages.success(request, f'Submission for "{target_assignment.title}" uploaded successfully!')
            return redirect('student_dashboard')
    else:
        form = SubmissionForm()
        
    context = {
        'student': student,
        'courses': current_courses,
        'assignments': assignments,
        'selected_assignment': selected_assignment,
        'form': form,
    }
    return render(request, 'submissions/upload_assignment.html', context)


@login_required
@user_passes_test(is_student)
def student_assignments(request):
    student = request.user.student_profile
    submissions = Submission.objects.filter(student=student).select_related(
        'assignment', 'assignment__course', 'grade_record'
    ).order_by('-date_uploaded')
    
    return render(request, 'submissions/student_assignments.html', {
        'submissions': submissions,
        'student': student
    })


@login_required
@user_passes_test(is_student)
def student_profile(request):
    student = request.user.student_profile
    if request.method == 'POST':
        form = StudentProfileEditForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('student_profile')
    else:
        form = StudentProfileEditForm(instance=student)
        
    return render(request, 'submissions/student_profile.html', {
        'student': student,
        'form': form
    })


@login_required
@user_passes_test(is_lecturer)
def lecturer_profile(request):
    lecturer = request.user.lecturer_profile
    if request.method == 'POST':
        form = LecturerProfileEditForm(request.POST, instance=lecturer)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('lecturer_profile')
    else:
        form = LecturerProfileEditForm(instance=lecturer)
        
    assignments = Assignment.objects.filter(created_by=lecturer).select_related('course', 'session', 'semester')
    
    return render(request, 'submissions/lecturer_profile.html', {
        'lecturer': lecturer,
        'form': form,
        'assignments': assignments,
    })


# ---------- Lecturer & Admin Views ----------
@login_required
@user_passes_test(is_lecturer)
def lecturer_dashboard(request):
    lecturer = request.user.lecturer_profile
    courses = Course.objects.filter(department=lecturer.department) if lecturer.department else Course.objects.none()
    assignments = Assignment.objects.filter(course__in=courses)
    submissions = Submission.objects.filter(assignment__in=assignments).select_related('student__user', 'assignment__course', 'grade_record')
    
    total_assignments = assignments.count()
    total_submissions = submissions.count()
    graded_submissions = submissions.filter(status='graded').count()
    pending_submissions = submissions.filter(status__in=['pending', 'under_review']).count()
    total_courses = courses.count()
    
    recent_submissions = submissions.order_by('-date_uploaded')[:10]
    
    context = {
        'lecturer': lecturer,
        'courses': courses,
        'total_assignments': total_assignments,
        'total_submissions': total_submissions,
        'graded_assignments': graded_submissions,
        'pending_assignments': pending_submissions,
        'total_courses': total_courses,
        'recent_submissions': recent_submissions,
        'recent_assignments': recent_submissions,
    }
    return render(request, 'submissions/admin_dashboard.html', context)


@login_required
@user_passes_test(is_lecturer)
def lecturer_assignments(request):
    lecturer = request.user.lecturer_profile
    status_filter = request.GET.get('status', 'all')
    
    courses = Course.objects.filter(department=lecturer.department) if lecturer.department else Course.objects.none()
    submissions = Submission.objects.filter(assignment__course__in=courses)
    
    if status_filter != 'all':
        submissions = submissions.filter(status=status_filter)
        
    submissions = submissions.select_related('student__user', 'assignment', 'assignment__course', 'grade_record').order_by('-date_uploaded')
    
    return render(request, 'submissions/lecturer_assignments.html', {
        'submissions': submissions,
        'lecturer': lecturer,
        'status_filter': status_filter
    })


@login_required
@user_passes_test(is_lecturer)
def create_assignment(request):
    lecturer = request.user.lecturer_profile
    if request.method == 'POST':
        form = AssignmentForm(request.POST, request.FILES, lecturer=lecturer)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.created_by = lecturer
            assignment.save()
            
            # Send notifications to students in that course
            students = StudentProfile.objects.filter(
                department=assignment.course.department,
                level=assignment.course.level
            )
            for student in students:
                Notification.objects.create(
                    recipient=student.user,
                    sender=request.user,
                    message=f'New assignment published: "{assignment.title}" in {assignment.course.code}.',
                    link='/student/dashboard/'
                )
                
            messages.success(request, f'Assignment "{assignment.title}" published successfully!')
            return redirect('lecturer_dashboard')
    else:
        form = AssignmentForm(lecturer=lecturer)
        
    return render(request, 'submissions/create_assignment.html', {
        'form': form,
        'lecturer': lecturer
    })


@login_required
@user_passes_test(is_lecturer)
def grade_assignment(request, assignment_id):
    # Parameter is named assignment_id in urls.py, but it maps to Submission ID
    lecturer = request.user.lecturer_profile
    submission = get_object_or_404(
        Submission,
        id=assignment_id,
        assignment__course__department=lecturer.department
    )
    
    grade_instance = getattr(submission, 'grade_record', None)
    
    if request.method == 'POST':
        form = GradeAssignmentForm(request.POST, instance=grade_instance)
        if form.is_valid():
            grade_obj = form.save(commit=False)
            grade_obj.submission = submission
            grade_obj.graded_by = lecturer
            grade_obj.save()
            
            status = form.cleaned_data.get('status', 'graded')
            submission.status = status
            submission.save()
            
            # Create notification for student
            Notification.objects.create(
                recipient=submission.student.user,
                sender=request.user,
                message=f'Your submission for "{submission.assignment.title}" has been graded ({grade_obj.grade}).',
                link='/student/assignments/'
            )
            
            messages.success(request, f'Grade submitted successfully for {submission.student.user.full_name}!')
            return redirect('lecturer_assignments')
    else:
        initial_status = submission.status
        form = GradeAssignmentForm(instance=grade_instance, initial={'status': initial_status})
        
    context = {
        'submission': submission,
        'form': form,
        'lecturer': lecturer,
    }
    return render(request, 'submissions/grade_assignment.html', context)


@login_required
@user_passes_test(is_lecturer)
def lecturer_courses(request):
    lecturer = request.user.lecturer_profile
    courses = Course.objects.filter(department=lecturer.department).select_related('department', 'level') if lecturer.department else Course.objects.none()
    
    return render(request, 'submissions/lecturer_courses.html', {
        'courses': courses,
        'lecturer': lecturer
    })


@login_required
@user_passes_test(is_lecturer)
def lecturer_students(request):
    lecturer = request.user.lecturer_profile
    students = StudentProfile.objects.filter(
        department=lecturer.department
    ).select_related('user', 'level').distinct()
    
    return render(request, 'submissions/lecturer_students.html', {
        'students': students,
        'lecturer': lecturer
    })


# ---------- Global Search ----------
@login_required
def global_search(request):
    query = request.GET.get('q', '').strip()
    results = {
        'students': [],
        'courses': [],
        'assignments': [],
        'departments': [],
        'lecturers': [],
    }
    
    if query:
        results['students'] = StudentProfile.objects.filter(
            Q(user__full_name__icontains=query) |
            Q(matric_number__icontains=query) |
            Q(user__email__icontains=query)
        ).select_related('user', 'department', 'level')[:10]
        
        results['courses'] = Course.objects.filter(
            Q(code__icontains=query) |
            Q(title__icontains=query)
        ).select_related('department', 'lecturer__user')[:10]
        
        results['assignments'] = Assignment.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query)
        ).select_related('course')[:10]
        
        results['departments'] = Department.objects.filter(
            Q(name__icontains=query) |
            Q(code__icontains=query)
        )[:10]
        
        results['lecturers'] = LecturerProfile.objects.filter(
            Q(user__full_name__icontains=query) |
            Q(staff_id__icontains=query) |
            Q(designation__icontains=query)
        ).select_related('user', 'department')[:10]
        
    return render(request, 'submissions/search_results.html', {
        'query': query,
        'results': results
    })


# ---------- Reports ----------
@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def reports_view(request):
    dept_submissions = Department.objects.annotate(
        sub_count=Count('courses__assignments__submissions')
    ).values('name', 'code', 'sub_count')
    
    grade_distribution = Grade.objects.values('grade').annotate(
        count=Count('id')
    ).order_by('grade')
    
    student_performance = StudentProfile.objects.annotate(
        avg_score=Avg('submissions__grade_record__score'),
        sub_count=Count('submissions')
    ).values('user__full_name', 'matric_number', 'avg_score', 'sub_count').order_by('-avg_score')[:20]

    export_format = request.GET.get('export', '')
    if export_format == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="student_performance_report.csv"'
        writer = csv.writer(response)
        writer.writerow(['Student Name', 'Matric Number', 'Average Score', 'Submissions Count'])
        for record in student_performance:
            writer.writerow([
                record['user__full_name'],
                record['matric_number'],
                record['avg_score'] or 'N/A',
                record['sub_count']
            ])
        return response
        
    context = {
        'dept_submissions': dept_submissions,
        'grade_distribution': grade_distribution,
        'student_performance': student_performance,
    }
    return render(request, 'submissions/reports.html', context)


# ---------- Notifications ----------
@login_required
def notifications_list(request):
    notifications = request.user.notifications.all()[:50]
    return render(request, 'submissions/notifications.html', {
        'notifications': notifications
    })


@login_required
@require_POST
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.is_read = True
    notification.save()
    return JsonResponse({'status': 'success'})


# ---------- REST API ViewSets ----------
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

class StudentViewSet(viewsets.ModelViewSet):
    queryset = StudentProfile.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if hasattr(self.request.user, 'student_profile'):
            return self.queryset.filter(user=self.request.user)
        elif hasattr(self.request.user, 'lecturer_profile'):
            return self.queryset.filter(department=self.request.user.lecturer_profile.department)
        return self.queryset.none()
    
    @action(detail=True, methods=['get'])
    def assignments(self, request, pk=None):
        student = self.get_object()
        submissions = Submission.objects.filter(student=student)
        return Response([{"id": s.id, "assignment": s.assignment.title, "status": s.status} for s in submissions])


class LecturerViewSet(viewsets.ModelViewSet):
    queryset = LecturerProfile.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if hasattr(self.request.user, 'lecturer_profile'):
            return self.queryset.filter(user=self.request.user)
        return self.queryset.none()
    
    @action(detail=True, methods=['get'])
    def courses(self, request, pk=None):
        lecturer = self.get_object()
        courses = Course.objects.filter(department=lecturer.department) if lecturer.department else Course.objects.none()
        return Response([{"id": c.id, "code": c.code, "title": c.title} for c in courses])


@login_required
def logout_view(request):
    logout(request)
    return redirect('login')

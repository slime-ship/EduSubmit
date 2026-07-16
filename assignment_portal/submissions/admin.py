from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    UserProfile, StudentProfile, LecturerProfile, 
    Faculty, Department, Level, Course, Assignment,
    AcademicSession, Semester, Submission, Grade, Notification
)
from django.utils.translation import gettext_lazy as _


class StudentProfileInline(admin.StackedInline):
    model = StudentProfile
    can_delete = False
    verbose_name_plural = 'Student Profile'
    fk_name = 'user'


class LecturerProfileInline(admin.StackedInline):
    model = LecturerProfile
    can_delete = False
    verbose_name_plural = 'Lecturer Profile'
    fk_name = 'user'


@admin.register(UserProfile)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'full_name', 'user_type', 'is_staff')
    list_filter = ('user_type', 'is_staff', 'is_active')
    search_fields = ('username', 'email', 'full_name')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('full_name', 'email', 'user_type')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'full_name', 'user_type', 'password1', 'password2'),
        }),
    )
    
    def get_inline_instances(self, request, obj=None):
        if not obj:
            return []
        if obj.user_type == 'student':
            return [StudentProfileInline(self.model, self.admin_site)]
        elif obj.user_type == 'lecturer':
            return [LecturerProfileInline(self.model, self.admin_site)]
        return []


@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    search_fields = ('name', 'code')


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'faculty', 'head_of_department')
    list_filter = ('faculty',)
    search_fields = ('name', 'code')
    autocomplete_fields = ['head_of_department']


@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('matric_number', 'user', 'faculty', 'department', 'level', 'admission_year')
    list_filter = ('faculty', 'department', 'level')
    search_fields = ('matric_number', 'user__full_name', 'user__email')
    autocomplete_fields = ['user', 'faculty', 'department', 'level']


# Custom Admin Site for Each Lecturer
class LecturerAdminSite(admin.AdminSite):
    def __init__(self, lecturer_profile, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lecturer_profile = lecturer_profile
        self.name = f'lecturer_{lecturer_profile.staff_id}'
    
    def has_permission(self, request):
        """
        Only allow access if the user is the lecturer
        """
        return (
            request.user.is_active and
            request.user.is_staff and
            hasattr(request.user, 'lecturer_profile') and
            request.user.lecturer_profile.id == self.lecturer_profile.id
        )


@admin.register(LecturerProfile)
class LecturerProfileAdmin(admin.ModelAdmin):
    list_display = ('staff_id', 'user', 'faculty', 'department', 'designation', 'is_department_head')
    list_filter = ('faculty', 'department', 'is_department_head')
    search_fields = ('staff_id', 'user__full_name', 'user__email')
    autocomplete_fields = ['user', 'faculty', 'department']
    
    def save_model(self, request, obj, form, change):
        """
        Create custom admin site for lecturer when profile is created/updated
        """
        super().save_model(request, obj, form, change)
        if not change:  # New lecturer
            # Make user a staff member
            obj.user.is_staff = True
            obj.user.save()
            
            lecturer_site = LecturerAdminSite(obj, name=f'lecturer_{obj.staff_id}')
            register_lecturer_admin_models(lecturer_site)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('code', 'title', 'department', 'level', 'lecturer', 'credit_units', 'is_active')
    list_filter = ('department', 'level', 'is_active')
    search_fields = ('code', 'title')
    autocomplete_fields = ['department', 'level', 'lecturer']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if hasattr(request.user, 'lecturer_profile') and not request.user.is_superuser:
            return qs.filter(lecturer=request.user.lecturer_profile)
        return qs


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'session', 'semester', 'deadline', 'created_by')
    list_filter = ('course', 'session', 'semester', 'deadline')
    search_fields = ('title', 'course__code', 'course__title')
    autocomplete_fields = ['course', 'session', 'semester', 'created_by']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if hasattr(request.user, 'lecturer_profile') and not request.user.is_superuser:
            return qs.filter(created_by=request.user.lecturer_profile)
        return qs

    def save_model(self, request, obj, form, change):
        if not obj.created_by and hasattr(request.user, 'lecturer_profile'):
            obj.created_by = request.user.lecturer_profile
        super().save_model(request, obj, form, change)


@admin.register(AcademicSession)
class AcademicSessionAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    search_fields = ('name',)


@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    search_fields = ('name',)


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('assignment', 'student', 'status', 'date_uploaded')
    list_filter = ('status', 'assignment__course')
    search_fields = ('assignment__title', 'student__matric_number')
    readonly_fields = ('date_uploaded', 'submission_date')
    autocomplete_fields = ['assignment', 'student']


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ('submission', 'grade', 'score', 'graded_by', 'graded_date')
    list_filter = ('grade', 'graded_by')
    search_fields = ('submission__assignment__title', 'submission__student__matric_number')
    autocomplete_fields = ['submission', 'graded_by']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'message', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('recipient__username', 'message')
    autocomplete_fields = ['recipient', 'sender']


def register_lecturer_admin_models(site):
    site.register(Course, CourseAdmin)
    site.register(Assignment, AssignmentAdmin)
    site.register(AcademicSession, AcademicSessionAdmin)
    site.register(Semester, SemesterAdmin)
    site.register(LecturerProfile, LecturerProfileAdmin)
    site.register(Department, DepartmentAdmin)
    site.register(Level, LevelAdmin)
    site.register(StudentProfile, StudentProfileAdmin)
    site.register(UserProfile, CustomUserAdmin)
    site.register(Faculty, FacultyAdmin)
    site.register(Submission, SubmissionAdmin)
    site.register(Grade, GradeAdmin)
    site.register(Notification, NotificationAdmin)

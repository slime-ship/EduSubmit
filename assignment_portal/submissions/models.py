from django.db import models
from cloudinary.models import CloudinaryField
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.contrib.auth import get_user_model

# ---------- Base User Models ----------
class BaseUserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError("Username is required")
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, password, **extra_fields)


class UserProfile(AbstractBaseUser, PermissionsMixin):
    USER_TYPES = [
        ('student', 'Student'),
        ('lecturer', 'Lecturer'),
        ('admin', 'Administrator'),
    ]
    
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=100)
    user_type = models.CharField(max_length=20, choices=USER_TYPES, default='student')
    date_joined = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    
    objects = BaseUserManager()
    
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'full_name']
    
    def __str__(self):
        return f"{self.username} ({self.user_type})"


# ---------- Academic Structure ----------
class Faculty(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name


class Department(models.Model):
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='departments')
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    head_of_department = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, 
                                          null=True, blank=True, related_name='headed_departments')
    
    class Meta:
        unique_together = ('faculty', 'name')
    
    def __str__(self):
        return f"{self.name} ({self.faculty.code})"


class Level(models.Model):
    LEVELS = [
        ('100', '100 Level'),
        ('200', '200 Level'),
        ('300', '300 Level'),
        ('400', '400 Level'),
        ('500', '500 Level'),
        ('600', '600 Level'),
    ]
    
    name = models.CharField(max_length=50, choices=LEVELS, unique=True)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name


# ---------- Student Profile ----------
class StudentProfile(models.Model):
    user = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='student_profile')
    matric_number = models.CharField(max_length=20, unique=True)
    faculty = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, related_name='students')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, related_name='students')
    level = models.ForeignKey(Level, on_delete=models.SET_NULL, null=True)
    admission_year = models.IntegerField()
    phone_number = models.CharField(max_length=15, blank=True)
    
    def __str__(self):
        return f"{self.matric_number} - {self.user.full_name}"


# ---------- Lecturer Profile ----------
class LecturerProfile(models.Model):
    user = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='lecturer_profile')
    staff_id = models.CharField(max_length=20, unique=True)
    faculty = models.ForeignKey(Faculty, on_delete=models.SET_NULL, null=True, related_name='lecturers')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, related_name='lecturers')
    designation = models.CharField(max_length=100)
    bio = models.TextField(blank=True)  # Add this line
    office_location = models.CharField(max_length=100, blank=True)
    office_hours = models.TextField(blank=True)
    phone_extension = models.CharField(max_length=10, blank=True)
    is_department_head = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.staff_id} - {self.user.full_name}"


# ---------- Course Model ----------
class Course(models.Model):
    code = models.CharField(max_length=10, unique=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    credit_units = models.IntegerField(default=3)
    deadline = models.DateTimeField(null=True, blank=True, help_text="Assignment submission deadline")
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='courses')
    level = models.ForeignKey(Level, on_delete=models.CASCADE, related_name='courses')
    lecturer = models.ForeignKey(LecturerProfile, on_delete=models.SET_NULL, null=True, 
                                related_name='courses_teaching')
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.code} - {self.title}"


# ---------- Academic Session & Semester ----------
class AcademicSession(models.Model):
    name = models.CharField(max_length=20, unique=True, help_text="e.g. 2025/2026")
    is_active = models.BooleanField(default=False)
    
    def __str__(self):
        return self.name
        
    def save(self, *args, **kwargs):
        if self.is_active:
            AcademicSession.objects.filter(is_active=True).update(is_active=False)
        super().save(*args, **kwargs)


class Semester(models.Model):
    SEMESTERS = [
        ('first', 'First Semester'),
        ('second', 'Second Semester'),
    ]
    name = models.CharField(max_length=20, choices=SEMESTERS, unique=True)
    is_active = models.BooleanField(default=False)
    
    def __str__(self):
        return self.get_name_display()
        
    def save(self, *args, **kwargs):
        if self.is_active:
            Semester.objects.filter(is_active=True).update(is_active=False)
        super().save(*args, **kwargs)


# ---------- Assignment Model (Lecturer Prompt) ----------
class Assignment(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assignments')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    file = CloudinaryField('file', null=True, blank=True, help_text="Supporting document or instructions")
    session = models.ForeignKey(AcademicSession, on_delete=models.CASCADE, related_name='assignments')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='assignments')
    deadline = models.DateTimeField(help_text="Due date and time")
    created_by = models.ForeignKey(LecturerProfile, on_delete=models.SET_NULL, null=True, related_name='created_assignments')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.title} - {self.course.code}"


# ---------- Submission Model (Student Upload) ----------
class Submission(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('under_review', 'Under Review'),
        ('graded', 'Graded'),
        ('returned', 'Returned for Revision'),
    ]
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='submissions')
    file = CloudinaryField('file', null=True, blank=True)
    date_uploaded = models.DateTimeField(auto_now_add=True)
    submission_date = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    class Meta:
        ordering = ['-date_uploaded']
        unique_together = ('assignment', 'student')
        
    def __str__(self):
        return f"{self.assignment.title} - {self.student.matric_number}"

    @property
    def course(self):
        return self.assignment.course

    @property
    def title(self):
        return self.assignment.title

    @property
    def description(self):
        return self.assignment.description

    @property
    def deadline(self):
        return self.assignment.deadline

    @property
    def grade(self):
        return self.grade_record.grade if hasattr(self, 'grade_record') else None

    @property
    def score(self):
        return self.grade_record.score if hasattr(self, 'grade_record') else None

    @property
    def feedback(self):
        return self.grade_record.feedback if hasattr(self, 'grade_record') else None

    @property
    def graded_by(self):
        return self.grade_record.graded_by if hasattr(self, 'grade_record') else None

    @property
    def graded_date(self):
        return self.grade_record.graded_date if hasattr(self, 'grade_record') else None


# ---------- Grade Model ----------
class Grade(models.Model):
    submission = models.OneToOneField(Submission, on_delete=models.CASCADE, related_name='grade_record')
    grade = models.CharField(max_length=5, choices=[
        ('A', 'A'),
        ('B', 'B'),
        ('C', 'C'),
        ('D', 'D'),
        ('F', 'F'),
    ])
    score = models.DecimalField(max_digits=5, decimal_places=2)
    feedback = models.TextField(blank=True, null=True)
    graded_by = models.ForeignKey(LecturerProfile, on_delete=models.SET_NULL, null=True, related_name='grades_given')
    graded_date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Grade {self.grade} ({self.score}) for {self.submission}"


# ---------- Notification Model ----------
class Notification(models.Model):
    recipient = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_notifications')
    message = models.TextField()
    link = models.CharField(max_length=255, blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"Notification for {self.recipient.username} - {self.message[:30]}"

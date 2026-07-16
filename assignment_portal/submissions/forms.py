from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.utils.translation import gettext_lazy as _
import os  # Added for file validation
from .models import (
    UserProfile, StudentProfile, LecturerProfile, 
    Faculty, Department, Level, Assignment, Submission, Grade, AcademicSession, Semester
)

class UserRegistrationForm(UserCreationForm):
    USER_TYPE_CHOICES = [
        ('student', 'Student'),
        ('lecturer', 'Lecturer'),
    ]
    
    user_type = forms.ChoiceField(
        choices=USER_TYPE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_user_type'
        })
    )
    
    full_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter your full name'
        })
    )
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter your university email'
        })
    )
    
    username = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Choose a username'
        })
    )
    
    # Student-specific fields
    matric_number = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Matric number (for students only)'
        })
    )
    
    admission_year = forms.IntegerField(  # ADD THIS FIELD
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-input',
            'placeholder': 'Admission year (e.g., 2023)',
            'min': '2000',
            'max': '2026'
        })
    )
    
    phone_number = forms.CharField(  # ADD THIS FIELD
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Phone number (optional)'
        })
    )
    
    # Lecturer-specific fields
    staff_id = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Staff ID (for lecturers only)'
        })
    )
    
    designation = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Designation (for lecturers only)'
        })
    )
    
    class Meta:
        model = UserProfile
        fields = ['username', 'email', 'full_name', 'user_type', 'password1', 'password2']
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if UserProfile.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if UserProfile.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username
    
    def clean(self):
        cleaned_data = super().clean()
        user_type = self.data.get('user_type', '')
        
        if user_type == 'student':
            matric_number = cleaned_data.get('matric_number')
            admission_year = cleaned_data.get('admission_year')
            
            if not matric_number:
                self.add_error('matric_number', 'Matric number is required for students.')
            else:
                import re
                matric_number = matric_number.strip().upper()
                cleaned_data['matric_number'] = matric_number
                pattern = r'^[A-Z0-9/\-_\. ]+$'
                if not re.match(pattern, matric_number):
                    self.add_error('matric_number', 'Matric number must contain only letters, digits, slashes, hyphens, underscores, dots, or spaces.')
                elif StudentProfile.objects.filter(matric_number=matric_number).exists():
                    self.add_error('matric_number', 'This matric number is already registered.')
            
            if not admission_year:  # Validate admission_year is provided
                self.add_error('admission_year', 'Admission year is required for students.')
        
        elif user_type == 'lecturer':
            staff_id = cleaned_data.get('staff_id')
            designation = cleaned_data.get('designation')
            
            if not staff_id:
                self.add_error('staff_id', 'Staff ID is required for lecturers.')
            elif LecturerProfile.objects.filter(staff_id=staff_id).exists():
                self.add_error('staff_id', 'This staff ID is already registered.')
            
            if not designation:
                self.add_error('designation', 'Designation is required for lecturers.')
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = self.cleaned_data['user_type']
        user.full_name = self.cleaned_data['full_name']
        
        if commit:
            user.save()
            # Create profile based on user type
            if user.user_type == 'student':
                StudentProfile.objects.create(
                    user=user,
                    matric_number=self.cleaned_data.get('matric_number', ''),
                    admission_year=self.cleaned_data.get('admission_year'),  # ADD THIS LINE
                    phone_number=self.cleaned_data.get('phone_number', '')    # ADD THIS LINE
                    # Note: faculty, department, level will be set in the complete_profile step
                )
            elif user.user_type == 'lecturer':
                LecturerProfile.objects.create(
                    user=user,
                    staff_id=self.cleaned_data.get('staff_id', ''),
                    designation=self.cleaned_data.get('designation', 'Lecturer')
                    # Note: faculty, department, etc. will be set in the complete_profile step
                )
                user.is_staff = True
                user.save()
        
        return user

class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(
        label=_('Username or Email'),
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter your username or email',
            'autocomplete': 'username',
            'autofocus': True,
        })
    )
    
    password = forms.CharField(
        label=_('Password'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter your password',
            'autocomplete': 'current-password',
        })
    )
    
    remember = forms.BooleanField(
        required=False,
        initial=True,
        label=_('Remember me'),
        widget=forms.CheckboxInput(attrs={
            'class': 'form-checkbox',
        })
    )


class StudentProfileForm(forms.ModelForm):
    faculty = forms.ModelChoiceField(
        queryset=Faculty.objects.all(),
        required=True,
        empty_label="Select Faculty",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_faculty'
        })
    )
    
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        required=True,
        empty_label="Select Department",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_department'
        })
    )
    
    level = forms.ModelChoiceField(
        queryset=Level.objects.all(),
        required=True,
        empty_label="Select Level",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_level'
        })
    )
    
    class Meta:
        model = StudentProfile
        fields = ['faculty', 'department', 'level', 'admission_year', 'phone_number']  # Changed from 'phone' to 'phone_number'
        widgets = {
            'admission_year': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g., 2023',
                'min': '2000',
                'max': '{% now "Y" %}'
            }),
            'phone_number': forms.TextInput(attrs={  # Changed from 'phone' to 'phone_number'
                'class': 'form-input',
                'placeholder': 'Phone number'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter departments based on selected faculty
        if 'faculty' in self.data:
            try:
                faculty_id = int(self.data.get('faculty'))
                self.fields['department'].queryset = Department.objects.filter(faculty_id=faculty_id)
            except (ValueError, TypeError):
                pass

class LecturerProfileForm(forms.ModelForm):
    faculty = forms.ModelChoiceField(
        queryset=Faculty.objects.all(),
        required=True,
        empty_label="Select Faculty",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_faculty'
        })
    )
    
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        required=True,
        empty_label="Select Department",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_department'
        })
    )
    
    class Meta:
        model = LecturerProfile
        fields = [
            'staff_id', 
            'faculty', 
            'department', 
            'designation', 
            'office_location',  # Changed from 'office'
            'office_hours',      # You might want to add this too
            'phone_extension',   # Changed from 'phone'
            'is_department_head'
        ]
        widgets = {
            'staff_id': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter staff ID'
            }),
            'designation': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g., Senior Lecturer, Professor'
            }),
            'office_location': forms.TextInput(attrs={  # Changed from 'office'
                'class': 'form-input',
                'placeholder': 'Office location'
            }),
            'office_hours': forms.Textarea(attrs={      # Added this
                'class': 'form-textarea',
                'placeholder': 'e.g., Monday 10am-12pm, Wednesday 2pm-4pm',
                'rows': 3
            }),
            'phone_extension': forms.TextInput(attrs={  # Changed from 'phone'
                'class': 'form-input',
                'placeholder': 'Phone extension'
            }),
            'is_department_head': forms.CheckboxInput(attrs={
                'class': 'form-checkbox'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter departments based on selected faculty
        if 'faculty' in self.data:
            try:
                faculty_id = int(self.data.get('faculty'))
                self.fields['department'].queryset = Department.objects.filter(faculty_id=faculty_id)
            except (ValueError, TypeError):
                pass

class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ['course', 'title', 'description', 'file', 'session', 'semester', 'deadline']
        widgets = {
            'course': forms.Select(attrs={'class': 'form-select'}),
            'session': forms.Select(attrs={'class': 'form-select'}),
            'semester': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter assignment title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-textarea',
                'placeholder': 'Optional instructions or description',
                'rows': 4
            }),
            'file': forms.ClearableFileInput(attrs={
                'class': 'file-input'
            }),
            'deadline': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-input'
            }),
        }
        
    def __init__(self, *args, **kwargs):
        lecturer = kwargs.pop('lecturer', None)
        super().__init__(*args, **kwargs)
        if lecturer:
            self.fields['course'].queryset = Course.objects.filter(lecturer=lecturer)
        self.fields['session'].queryset = AcademicSession.objects.all()
        self.fields['semester'].queryset = Semester.objects.all()


class SubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ['file']
        widgets = {
            'file': forms.ClearableFileInput(attrs={
                'class': 'file-input'
            }),
        }
        
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Validate file size (20MB)
            max_size = 20 * 1024 * 1024  # 20MB
            if file.size > max_size:
                raise forms.ValidationError("File size must not exceed 20MB.")
            
            # Validate file type
            allowed_extensions = ['.pdf', '.doc', '.docx', '.ppt', '.pptx', '.txt', '.zip', '.rar']
            ext = os.path.splitext(file.name)[1].lower()
            if ext not in allowed_extensions:
                raise forms.ValidationError(
                    f"File type not supported. Allowed types: {', '.join(allowed_extensions)}"
                )
        else:
            raise forms.ValidationError("You must upload a file.")
        return file


class GradeAssignmentForm(forms.ModelForm):
    status = forms.ChoiceField(
        choices=Submission.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    score = forms.DecimalField(
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(attrs={
            'class': 'form-input',
            'step': '0.1'
        })
    )
    
    class Meta:
        model = Grade
        fields = ['grade', 'score', 'feedback']
        widgets = {
            'grade': forms.Select(choices=[
                ('A', 'A'),
                ('B', 'B'),
                ('C', 'C'),
                ('D', 'D'),
                ('F', 'F'),
            ], attrs={'class': 'form-select'}),
            'feedback': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 4,
                'placeholder': 'Provide feedback to the student'
            }),
        }


class StudentProfileEditForm(forms.ModelForm):
    full_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-input block w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 focus:outline-none transition-colors',
            'placeholder': 'Full Name'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-input block w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 focus:outline-none transition-colors',
            'placeholder': 'Email Address'
        })
    )
    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-input block w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 focus:outline-none transition-colors',
            'placeholder': 'Leave blank to keep current password'
        }),
        help_text="Leave blank if you do not want to change your password."
    )
    confirm_password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-input block w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 focus:outline-none transition-colors',
            'placeholder': 'Confirm new password'
        })
    )

    class Meta:
        model = StudentProfile
        fields = ['phone_number']
        widgets = {
            'phone_number': forms.TextInput(attrs={
                'class': 'form-input block w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 focus:outline-none transition-colors',
                'placeholder': 'Phone Number'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['full_name'].initial = self.instance.user.full_name
            self.fields['email'].initial = self.instance.user.email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password or confirm_password:
            if password != confirm_password:
                self.add_error('confirm_password', 'Passwords do not match.')

        # Email uniqueness check
        email = cleaned_data.get('email')
        if email:
            qs = UserProfile.objects.filter(email=email)
            if self.instance and self.instance.user:
                qs = qs.exclude(id=self.instance.user.id)
            if qs.exists():
                self.add_error('email', 'This email is already taken.')

        return cleaned_data

    def save(self, commit=True):
        student_profile = super().save(commit=False)
        user = student_profile.user
        user.full_name = self.cleaned_data['full_name']
        user.email = self.cleaned_data['email']
        
        password = self.cleaned_data.get('password')
        if password:
            user.set_password(password)
            
        if commit:
            user.save()
            student_profile.save()
        return student_profile
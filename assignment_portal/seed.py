import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'assignment_portal.settings')
django.setup()

from django.contrib.auth import get_user_model
from submissions.models import (
    Faculty, Department, Level, StudentProfile, LecturerProfile,
    Course, AcademicSession, Semester, Assignment, Submission, Grade
)
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

def seed_data():
    print("Seeding database...")
    
    # 1. Academic Sessions
    session_active, _ = AcademicSession.objects.get_or_create(
        name="2025/2026",
        defaults={"is_active": True}
    )
    session_inactive, _ = AcademicSession.objects.get_or_create(
        name="2026/2027",
        defaults={"is_active": False}
    )
    print("Academic Sessions created.")

    # 2. Semesters
    semester_active, _ = Semester.objects.get_or_create(
        name="first",
        defaults={"is_active": True}
    )
    semester_inactive, _ = Semester.objects.get_or_create(
        name="second",
        defaults={"is_active": False}
    )
    print("Semesters created.")

    # 3. Levels
    levels = ["100", "200", "300", "400", "500", "600"]
    level_objs = {}
    for name in levels:
        lvl, _ = Level.objects.get_or_create(name=name, defaults={"description": f"{name} Level Students"})
        level_objs[name] = lvl
    print("Levels created.")

    # 4. Faculties & Departments
    faculty_science, _ = Faculty.objects.get_or_create(name="Science", code="SCI")
    faculty_eng, _ = Faculty.objects.get_or_create(name="Engineering", code="ENG")
    
    dept_cs, _ = Department.objects.get_or_create(
        faculty=faculty_science,
        name="Computer Science",
        code="CSC"
    )
    dept_ee, _ = Department.objects.get_or_create(
        faculty=faculty_eng,
        name="Electrical Engineering",
        code="EEE"
    )
    print("Faculties and Departments created.")

    # 5. Users (Admin, Lecturers, Students)
    # Admin
    if not User.objects.filter(username="admin").exists():
        admin = User.objects.create_superuser(username="admin", password="admin123", email="admin@edumanage.edu")
        admin.full_name = "Super Admin"
        admin.user_type = "admin"
        admin.save()
        print("Super Admin created.")
        
    # Lecturer 1 User
    lec1_user, created = User.objects.get_or_create(
        username="lecturer01",
        defaults={
            "email": "lec1@edumanage.edu",
            "full_name": "Dr. John Doe",
            "user_type": "lecturer",
            "is_staff": True
        }
    )
    if created:
        lec1_user.set_password("demo123")
        lec1_user.save()
        
    # Lecturer 1 Profile
    lec1_profile, _ = LecturerProfile.objects.get_or_create(
        user=lec1_user,
        defaults={
            "staff_id": "STF001",
            "faculty": faculty_science,
            "department": dept_cs,
            "designation": "Senior Lecturer",
            "office_location": "Science Block A, Room 302",
            "office_hours": "Mon/Wed 10:00 AM - 12:00 PM"
        }
    )
    
    # Lecturer 2 User
    lec2_user, created = User.objects.get_or_create(
        username="lecturer02",
        defaults={
            "email": "lec2@edumanage.edu",
            "full_name": "Prof. Jane Smith",
            "user_type": "lecturer",
            "is_staff": True
        }
    )
    if created:
        lec2_user.set_password("demo123")
        lec2_user.save()
        
    # Lecturer 2 Profile
    lec2_profile, _ = LecturerProfile.objects.get_or_create(
        user=lec2_user,
        defaults={
            "staff_id": "STF002",
            "faculty": faculty_eng,
            "department": dept_ee,
            "designation": "Professor",
            "office_location": "Engineering Lab, Room 105",
            "office_hours": "Tue/Thu 2:00 PM - 4:00 PM"
        }
    )
    print("Lecturers created.")

    # Student 1 User
    std1_user, created = User.objects.get_or_create(
        username="student01",
        defaults={
            "email": "std1@edumanage.edu",
            "full_name": "Alice Williams",
            "user_type": "student"
        }
    )
    if created:
        std1_user.set_password("demo123")
        std1_user.save()
        
    # Student 1 Profile
    std1_profile, _ = StudentProfile.objects.get_or_create(
        user=std1_user,
        defaults={
            "matric_number": "UAT23/03/04/3001",
            "faculty": faculty_science,
            "department": dept_cs,
            "level": level_objs["300"],
            "admission_year": 2023,
            "phone_number": "+2348011223344"
        }
    )

    # Student 2 User
    std2_user, created = User.objects.get_or_create(
        username="student02",
        defaults={
            "email": "std2@edumanage.edu",
            "full_name": "Bob Johnson",
            "user_type": "student"
        }
    )
    if created:
        std2_user.set_password("demo123")
        std2_user.save()
        
    # Student 2 Profile
    std2_profile, _ = StudentProfile.objects.get_or_create(
        user=std2_user,
        defaults={
            "matric_number": "UAT23/03/04/3002",
            "faculty": faculty_eng,
            "department": dept_ee,
            "level": level_objs["300"],
            "admission_year": 2023,
            "phone_number": "+2348099887766"
        }
    )
    print("Students created.")

    # 6. Courses
    c1, _ = Course.objects.get_or_create(
        code="CSC301",
        defaults={
            "title": "Advanced Programming",
            "description": "Object-oriented programming and application development",
            "credit_units": 3,
            "department": dept_cs,
            "level": level_objs["300"],
            "lecturer": lec1_profile
        }
    )
    c2, _ = Course.objects.get_or_create(
        code="CSC305",
        defaults={
            "title": "Database Systems",
            "description": "SQL and relational database management systems",
            "credit_units": 3,
            "department": dept_cs,
            "level": level_objs["300"],
            "lecturer": lec1_profile
        }
    )
    c3, _ = Course.objects.get_or_create(
        code="EEE301",
        defaults={
            "title": "Circuit Theory II",
            "description": "AC circuits, frequency response, networks",
            "credit_units": 4,
            "department": dept_ee,
            "level": level_objs["300"],
            "lecturer": lec2_profile
        }
    )
    print("Courses created.")

    # 7. Assignments (Prompts)
    a1, _ = Assignment.objects.get_or_create(
        course=c1,
        title="Assignment 1: Design Patterns",
        defaults={
            "description": "Implement Singleton, Factory, and Observer patterns in Python.",
            "session": session_active,
            "semester": semester_active,
            "deadline": timezone.now() + timedelta(days=7),
            "created_by": lec1_profile
        }
    )
    a2, _ = Assignment.objects.get_or_create(
        course=c2,
        title="Assignment 1: Schema Normalization",
        defaults={
            "description": "Normalize the given tables to 3NF and BCNF.",
            "session": session_active,
            "semester": semester_active,
            "deadline": timezone.now() + timedelta(days=5),
            "created_by": lec1_profile
        }
    )
    print("Assignments created.")

    print("Database seeding completed successfully.")

if __name__ == "__main__":
    seed_data()

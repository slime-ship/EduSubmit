from django.test import TestCase
from submissions.forms import UserRegistrationForm, SubmissionForm, GradeAssignmentForm
from django.core.files.uploadedfile import SimpleUploadedFile

class FormValidationTestCase(TestCase):
    def test_matric_number_validation(self):
        # Valid format
        form_data = {
            'username': 'student_test',
            'email': 'student_test@edu.com',
            'full_name': 'Test Student',
            'user_type': 'student',
            'matric_number': 'UAT23/03/04/3001',
            'admission_year': 2023,
            'password1': 'testpass123',
            'password2': 'testpass123',
        }
        form = UserRegistrationForm(data=form_data)
        # Note: clean() will run and check unique constraints, and regex format
        self.assertTrue(form.is_valid(), form.errors)

        # Invalid format
        form_data_invalid = form_data.copy()
        form_data_invalid['matric_number'] = 'INVALID123'
        form_invalid = UserRegistrationForm(data=form_data_invalid)
        self.assertFalse(form_invalid.is_valid())
        self.assertIn('matric_number', form_invalid.errors)

    def test_submission_file_validation(self):
        # 1. Invalid extension
        txt_file = SimpleUploadedFile("assignment.mp3", b"some content", content_type="audio/mpeg")
        form = SubmissionForm(files={'file': txt_file})
        self.assertFalse(form.is_valid())
        self.assertIn('file', form.errors)

        # 2. Valid extension
        pdf_file = SimpleUploadedFile("assignment.pdf", b"some pdf content", content_type="application/pdf")
        form_valid = SubmissionForm(files={'file': pdf_file})
        self.assertTrue(form_valid.is_valid(), form_valid.errors)

    def test_grade_validation(self):
        # Invalid score
        form_data = {
            'grade': 'A',
            'score': 105.0,  # Max is 100
            'feedback': 'Good job',
            'status': 'graded',
        }
        form = GradeAssignmentForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('score', form.errors)

        # Valid score
        form_data_valid = {
            'grade': 'A',
            'score': 95.0,
            'feedback': 'Good job',
            'status': 'graded',
        }
        form_valid = GradeAssignmentForm(data=form_data_valid)
        self.assertTrue(form_valid.is_valid(), form_valid.errors)

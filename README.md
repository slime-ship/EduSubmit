# EduSubmit - Digital Assignment Portal

EduSubmit is a modern digital assignment management system built using **Python Django**, **PostgreSQL**, **HTML5**, **CSS3**, **JavaScript (Alpine.js)**, and **Tailwind CSS**. It allows students to submit assignment files online while lecturers can create assignments, review submissions, and provide grades/comments dynamically.

---

## Features
- **Student Dashboard**: Submit assignments, track grades, and view notification alerts.
- **Lecturer Dashboard**: Create assignment prompts, manage student submissions, and grade work.
- **REST API endpoints**: Accessible at `/api/students/` and `/api/lecturers/`.
- **System Reports**: CSV export of student performance and grades distribution.

---

## 🚀 Local Development Setup (Without Docker)

### 1. Prerequisites
- Python 3.10+
- PostgreSQL database (or Supabase instance)

### 2. Install Dependencies
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 3. Environment Variables
Create a `.env` file in the project root:
```env
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
DB_SSLMODE=disable
SECRET_KEY=your_secret_key
DEBUG=True
```

### 4. Database Setup & Seeding
```bash
# Navigate to project folder
cd assignment_portal

# Apply migrations
python manage.py migrate

# Seed initial academic sessions/semesters/mock data
python seed.py
```

### 5. Run Server
```bash
python manage.py runserver
```

---

## 🐳 Docker Deployment Setup (Recommended)

### 1. Run using Docker Compose
To spin up both the Django web application and a local PostgreSQL database container:

```bash
# Build and start services
docker-compose up --build
```
This binds the web application to `http://localhost:8000/`.

### 2. Apply Migrations & Seed DB inside Docker
```bash
# Run migrations
docker-compose exec web python manage.py migrate

# Seed data
docker-compose exec web python seed.py
```

---

## 🛠 Production Deployment

### 1. Build and Run single Docker Container
If deploying to platforms like **Render**, **Railway**, **AWS ECS**, or **Google Cloud Run**, build the Dockerfile:

```bash
docker build -t edusubmit:latest .
```

### 2. Environment Variables checklist for Production
Make sure to configure the following environment variables on your host:
- `DEBUG=False`
- `SECRET_KEY=a-secure-random-key`
- `DB_HOST=your-production-db-host`
- `DB_NAME=your-production-db-name`
- `DB_USER=your-production-db-user`
- `DB_PASSWORD=your-production-db-password`
- `DB_PORT=5432`
- `DB_SSLMODE=require`
- `ALLOWED_HOSTS=yourdomain.com`
- Cloudinary credentials (if uploading files to Cloudinary)

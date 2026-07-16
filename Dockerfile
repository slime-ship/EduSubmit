# Stage 1: Build dependency wheels
FROM python:3.11-slim as builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install compiler dependencies needed for psycopg2 / other packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Generate wheels for fast installation in next stage
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt


# Stage 2: Final runtime container
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PORT 8000

# Install postgres client runtime libraries and curl
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy generated wheels from builder and install them
COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache /wheels/*

# Copy the project files
COPY . .

# Set working directory to the Django project root
WORKDIR /app/assignment_portal

# Collect static files (with dummy values so it does not connect to DB during build)
RUN SECRET_KEY=dummy-key-for-build python manage.py collectstatic --noinput --clear

# Expose port
EXPOSE 8000

# Gunicorn cmd for production deployment
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "assignment_portal.wsgi:application"]

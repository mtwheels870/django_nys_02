# Use a Python base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_DIR=django_nys_02

# Create and set the working directory
WORKDIR /app

RUN apt-get update && apt-get install -y build-essential && \
    apt-get install -y libgdal-dev python3-gdal


RUN chown 1000:1000 /app
# 34.37 ERROR: Could not install packages due to an OSError: [Errno 13] Permission denied: '/.local'
# RUN chown 1000:1000 /.local

# Copy requirements file and install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the project files
#RUN mkdir $DJANGO_DIR 
COPY $DJANGO_DIR /app/

# RUN cd /app/$DJANGO_DIR

USER 1000

# Expose the port Django runs on
EXPOSE 8000

# Command to run the Django application
#CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
CMD ["tail", "-f", "/dev/null"]

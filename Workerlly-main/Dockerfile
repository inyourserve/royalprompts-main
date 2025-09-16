# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install system dependencies required for WeasyPrint
RUN apt-get update && apt-get install -y \
    build-essential \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libpangoft2-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    libglib2.0-0 \
    shared-mime-info \
    python3-dev \
    python3-cffi \
    libxml2-dev \
    libxslt-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip

# Install WeasyPrint and Python dependencies
RUN pip install --no-cache-dir pymongo==4.1.1
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Run uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

#FROM python:3.10-slim
#
## Set the working directory in the container
#WORKDIR /app
#
## Copy the current directory contents into the container at /app
#COPY . /app
#
## Install system dependencies
#RUN apt-get update && apt-get install -y \
#    build-essential \
#    && apt-get clean \
#    && rm -rf /var/lib/apt/lists/*
#
## Ensure pip is upgraded
#RUN pip install --upgrade pip
#
## Install necessary packages
#RUN pip install --no-cache-dir pymongo==4.1.1
#
## Install any needed packages specified in requirements.txt
#RUN pip install --no-cache-dir -r requirements.txt
#
## Make port 8000 available to the world outside this container
#EXPOSE 8000
#
## Run uvicorn
#CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
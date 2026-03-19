# Dockerfile for NeuroOps – RAG Platform

# Use official Python slim image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy pyproject.toml and install dependencies
COPY pyproject.toml /app/pyproject.toml
RUN pip install --no-cache-dir -U pip && pip install --no-cache-dir .

# Copy application source code
COPY src /app/src

# Expose port 8000 for the application
EXPOSE 8000

# Command to run the application using Uvicorn
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]

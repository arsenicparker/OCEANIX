# Dockerfile for OCEANIX prototype
# -------------------------------------------------
# Use the official lightweight Python image.
FROM python:3.12-slim

# Set a non‑root user for security.
RUN useradd -m appuser && mkdir -p /app && chown appuser:appuser /app
USER appuser
WORKDIR /app

# Install system dependencies required by some Python packages (e.g., pandas, scipy).
# No extra packages are needed for the current requirements, but keep this as a placeholder.

# Copy only the required files to leverage Docker cache for dependencies.
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the entire source tree.
COPY . ./

# Expose the FastAPI port.
EXPOSE 8000

# Default command to start the API server.
CMD ["uvicorn", "oceanix.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

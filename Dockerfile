# Use an explicit, stable slim Python runtime variant
FROM python:3.11-slim

# Set system optimization variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Establish our working directory context inside the container
WORKDIR /app

# Install system dependencies required for handling robust tracking components
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install package dependencies first to optimize Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files into the working directory
COPY . .

# Expose the standard routing port that Streamlit uses
EXPOSE 8501

# Run safety health checks to ensure container availability status
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Define runtime launch instruction variables
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]

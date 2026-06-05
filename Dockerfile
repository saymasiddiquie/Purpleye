FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy configuration and project files
COPY pyproject.toml README.md ./
COPY services/ ./services/
COPY config/ ./config/
COPY scripts/ ./scripts/

# Install the package and its runtime dependencies
RUN pip install --no-cache-dir -e .

# Expose the dashboard port (Streamlit defaults to 8501)
EXPOSE 8501
# Expose the internal API port
EXPOSE 8000

# Set executable permission for the production runner script
RUN chmod +x scripts/start_production.py

# Run the unified production stack coordinator
CMD ["python", "scripts/start_production.py"]

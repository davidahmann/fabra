FROM python:3.9-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy project files
COPY pyproject.toml .
COPY README.md .
COPY src/ src/

COPY examples/ examples/

# Install dependencies and project
RUN uv pip install --system .[ui]

# Run as non-root user
RUN useradd -m -s /bin/bash meridian
USER meridian

# Expose port
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl -f http://0.0.0.0:8000/health || exit 1

# Default command
CMD ["meridian", "serve", "examples/basic_features.py", "--host", "0.0.0.0", "--port", "8000"]

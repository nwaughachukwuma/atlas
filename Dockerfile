FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install uv for faster dependency management
RUN pip install uv

# Copy project files
COPY pyproject.toml .
COPY src/ ./src/
COPY README.md .
COPY LICENSE .

# Install the package
RUN uv pip install --system -e .

# Set up volume for vector store
VOLUME ["/root/atlas"]

# Default command
ENTRYPOINT ["atlas"]
CMD ["--help"]
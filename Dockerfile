# Use Playwright's Python image with all browsers pre-installed
FROM mcr.microsoft.com/playwright/python:v1.42.0-jammy

# Set working directory
WORKDIR /app

# Copy Poetry config and install dependencies
COPY pyproject.toml poetry.lock* ./
RUN pip install poetry && poetry install --no-root

# Copy the rest of the project files
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Start the FastAPI app (adjust if your entrypoint is not main.py)
CMD ["poetry", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

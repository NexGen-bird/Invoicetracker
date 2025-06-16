# Start from a base Playwright image with Python + browsers
FROM mcr.microsoft.com/playwright/python:v1.42.0-jammy

# Set workdir
WORKDIR /app

# Install curl (required to install Poetry)
RUN apt-get update && apt-get install -y curl

# Install Poetry the official way
RUN curl -sSL https://install.python-poetry.org | python3 -

# Add Poetry to PATH
ENV PATH="/root/.local/bin:$PATH"

# Copy project files
COPY pyproject.toml poetry.lock* ./

# Install dependencies without installing the project as a package
RUN poetry config virtualenvs.create false \
  && poetry install --no-root

# Copy the rest of the project
COPY . .

# Expose port
EXPOSE 8000

# Run FastAPI via Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

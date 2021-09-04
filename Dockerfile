FROM --platform=linux/amd64 python:3.9-slim

# Allow service to handle stops gracefully
STOPSIGNAL SIGQUIT

# Install C compiler and make
RUN apt-get update && \
    apt-get install -y gcc make && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Copy dependencies-related files
COPY poetry.lock .
COPY pyproject.toml .

# Install dependencies
RUN poetry config virtualenvs.create false
RUN poetry install --no-dev

# Copy all files to container
WORKDIR /app
COPY . .

# Set Git SHA build argument
ARG git_sha="development"

# Set Git SHA environment variable
ENV GIT_SHA=$git_sha

# Start the server with uvicorn
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:8000", "-k", "uvicorn.workers.UvicornWorker", "backend:app"]

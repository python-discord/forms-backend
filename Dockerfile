FROM python:3.9-slim

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

# Start the server with uvicorn
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:8000", "-k", "uvicorn.workers.UvicornWorker", "backend:app"]

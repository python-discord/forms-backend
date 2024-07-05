FROM --platform=linux/amd64 ghcr.io/owl-corp/python-poetry-base:3.12-slim

# Allow service to handle stops gracefully
STOPSIGNAL SIGQUIT

# Install C compiler and make
RUN apt-get update && \
    apt-get install -y gcc make && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install dependencies
WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN poetry install  --without dev

# Copy all files to container
COPY . .

# Set Git SHA build argument
ARG git_sha="development"

# Set Git SHA environment variable
ENV GIT_SHA=$git_sha

# Start the server with uvicorn
ENTRYPOINT ["poetry", "run"]
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:8000", "-k", "uvicorn.workers.UvicornWorker", "backend:app"]

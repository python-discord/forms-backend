FROM --platform=linux/amd64 ghcr.io/owl-corp/python-poetry-base:3.12-slim

# Allow service to handle stops gracefully
STOPSIGNAL SIGQUIT

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
ENTRYPOINT ["/bin/bash", "-c"]
CMD ["poetry run alembic upgrade head && poetry run uvicorn backend:app --host 0.0.0.0 --port 8000"]

# Python Discord Forms (Backend)
API for Python Discord forms (https://forms.pythondiscord.com) that handles Discord login and forms, submissions.

## Setup
### Prerequisites
To start working on forms-backend, you need few things:
1. Discord Application (in [Developers Portal](https://discord.com/developers/applications))
2. Poetry
3. Docker and docker-compose (optional)
4. Running MongoDB instance (when not using Docker)

### Running with Docker
Easiest way to run this is using Docker (and docker-compose).

#### Environment variables
Set following environment variables to `.env` file:
- `OAUTH2_CLIENT_ID`: Client ID of Discord Application (prerequisites point 1).
- `OAUTH2_CLIENT_SECRET`: Client Secret of Discord Application (prerequisites point 1).
- `ALLOWED_URL`: Allowed origin for CORS middleware.

#### Running
Running is really for this way: `docker-compose up`! And this is all: You can access now API from `http://localhost:8000`.

### Running on host
Another way to run forms-backend is manually in host.

#### Environment variables
First all same than in Docker environment variables section, with following additions:
- `DATABASE_URL`: MongoDB instance URI, in format `mongodb://(username):(password)@(database IP or domain):(port)`.
- `MONGO_DB`: MongoDB database name, defaults to `pydis_forms`.

#### Running
Almost same easy than for Docker: `uvicorn --reload --host 0.0.0.0 --debug "backend:app`.

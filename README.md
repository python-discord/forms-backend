# Python Discord Forms API
API for [Python Discord Forms](https://forms.pythondiscord.com) that handles Discord OAuth2 integration and form submission.

## Setup
### Prerequisites
To start working on forms-backend, you'll need few things:
1. Discord OAuth2 Application (from the [Discord Developers Portal](https://discord.com/developers/applications))
2. Poetry
3. Docker and docker-compose (optional)
4. Running MongoDB instance (when not using Docker)

### Running with Docker
The easiest way to run forms-backend is using Docker (and docker-compose).

#### Environment variables
Create a `.env` file in the root with the following values inside it (each variable should be a line like `VARIABLE=value`):
- `OAUTH2_CLIENT_ID`: Client ID of Discord OAuth2 Application (see prerequisites).
- `OAUTH2_CLIENT_SECRET`: Client Secret of Discord OAuth2 Application (see prerequisites).
- `ALLOWED_URL`: Allowed origin for CORS middleware.

#### Running
To start using the application, simply run `docker-compose up` in the repository root. You'll be able to access the application by visiting http://localhost:8000/

### Running on host
You can also run forms-backend manually on the host.

#### Environment variables
Create a `.env` file with the same contents as the Docker section above and the following new variables:
- `DATABASE_URL`: MongoDB instance URI, in format `mongodb://(username):(password)@(database IP or domain):(port)`.
- `MONGO_DB`: MongoDB database name, defaults to `pydis_forms`.

#### Running
Simply run: `$ uvicorn --reload --host 0.0.0.0 --debug backend:app`.

Once this is running the API will live-reload on any changes.

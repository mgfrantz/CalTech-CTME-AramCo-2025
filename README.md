# CalTech CTME: LLMs in Production Labs

Resources and labs for the September 2025 CalTech CTME course

## Local Setup

### 1. Instiall `uv`

UV is a fast Python dependency and project manager that we will be using for the course.
Please install using [these instructions](https://docs.astral.sh/uv/getting-started/installation/).

Once you've installed `uv`, run `uv venv` at the root of the repository.
This will be the active python environment we will use.
To activate it, run `source .venv/bin/activate` from the root of the repository.

### 2. Configure your `.env` file

Find `.env.template` at the root of the repository.
Run the following command to create the `.env` file we will use to populate required environment variables.

```bash
cp .env.template .env
```

Then, based the services we are using, populate the required environment variables in your `.env` file.
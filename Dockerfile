FROM ghcr.io/astral-sh/uv:python3.13-alpine

WORKDIR /app

COPY pyproject.toml uv.lock /app/
RUN uv sync --locked --no-cache --no-dev

COPY extensions.py main.py settings.py ./
CMD ["uv","run","./main.py"]
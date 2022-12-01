FROM python:3.10-alpine
RUN mkdir /app
WORKDIR /app
RUN pip install poetry && poetry config virtualenvs.create false
COPY poetry.lock pyproject.toml /app/
RUN poetry install -n --no-root --only main --no-cache
COPY . ./
CMD ["python","-u","./main.py"]
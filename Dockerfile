FROM python:3.9-alpine

WORKDIR /usr/src/app

COPY poetry.lock pyproject.toml ./

RUN apk add --no-cache gcc musl-dev python3-dev libffi-dev openssl-dev cargo && pip install --no-cache-dir poetry && poetry config virtualenvs.create false && poetry install --no-root --no-interaction --no-ansi -vvv && apk del gcc musl-dev python3-dev libffi-dev openssl-dev cargo
COPY . .

WORKDIR /usr/src/app/robocop_ng

CMD [ "python", "./__init__.py" ]

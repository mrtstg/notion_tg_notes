FROM python:3.11 AS builder
ENV PYTHONUNBUFFERED=1
WORKDIR /usr/src/app
COPY poetry.lock pyproject.toml ./
RUN pip3 install --no-cache-dir poetry==1.4.2
RUN poetry export --without-hashes --without dev,test -f requirements.txt -o requirements.txt
RUN python -m pip install --upgrade pip
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

FROM python:3.11-slim
ENV TZ=Europe/Moscow
ENV LANG C.UTF-8
WORKDIR /usr/src/app
COPY . .
COPY --from=builder /app/wheels /wheels
COPY --from=builder /usr/src/app/requirements.txt .
RUN pip install --no-cache /wheels/*
CMD $LAUNCH_COMMAND

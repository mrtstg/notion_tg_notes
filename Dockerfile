FROM python:3.11-slim
ENV TZ=Europe/Moscow
ENV LANG C.UTF-8
RUN pip3 install poetry
RUN poetry config virtualenvs.create false
WORKDIR /usr/src/app
COPY . .
RUN poetry install --no-interaction --no-ansi
CMD python src/main.py

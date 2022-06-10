FROM python:3.8.13-slim-buster

MAINTAINER Jero Schaefer "jeschaef@cs.uni-frankfurt.de"

WORKDIR /app

COPY ./requirements.txt requirements.txt

ENV BUILD_DEPS="build-essential" APP_DEPS="curl libpq-dev"

RUN apt-get update \
    && apt-get install -y ${BUILD_DEPS} ${APP_DEPS} --no-install-recommends \
    && pip install -r requirements.txt \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /usr/share/doc \
    && rm -rf /usr/share/man \
    && apt-get purge -y --auto-remove ${BUILD_DEPS} \
    && apt-get clean

RUN pip install gunicorn

ARG FLASK_ENV="production"
ENV FLASK_ENV="${FLASK_ENV}" PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

COPY . .

#RUN pip install --editable .

EXPOSE 8000

CMD ["gunicorn", "-c", "python:app.conf.gunicorn", "app.__init__:create_app()"]
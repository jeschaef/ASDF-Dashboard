FROM ubuntu:18.04

MAINTAINER Jero Schaefer "jeschaef@cs.uni-frankfurt.de"

RUN apt-get update -y && apt-get install -y python-pip python-dev

COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip install -r requirements.txt

COPY . /app

ENTRYPOINT ["python"]

CMD ["__init.py__"]
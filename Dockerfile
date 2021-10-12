FROM python:3.9

RUN   mkdir -p /srv/vims-code \
    && mkdir -p /srv/vims-code/logs/old

WORKDIR     /srv/vims-code

# Dockerize - tool for waiting DB
RUN   apt-get update && apt-get install -y wget
ARG   DOCKERIZE_VERSION="v0.6.1"
ENV   DOCKERIZE_VERSION=${DOCKERIZE_VERSION}
RUN   wget --quiet https://github.com/jwilder/dockerize/releases/download/$DOCKERIZE_VERSION/dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
    && tar -C /usr/local/bin -xzvf dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
    && rm dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz

RUN   mkdir -p /srv/vims-code \
    && mkdir -p /srv/vims-code/logs/old

ENV PG_HOST=postgresql://vims:vims@db:5432/vims
ENV SQL_HOST=db
ENV SQL_PORT=5432

WORKDIR     /srv/vims-code

# install dependencies
RUN     pip install --upgrade pip
# COPY    ./requirements.txt .
# RUN     pip install -r requirements.txt
RUN     pip install poetry
COPY    ./pyproject.toml .
RUN     poetry update
RUN     apt-get install -y abiword
RUN curl -fsSL -o /usr/local/bin/dbmate https://github.com/amacneil/dbmate/releases/latest/download/dbmate-linux-amd64
RUN chmod +x /usr/local/bin/dbmate
# copy code
COPY     . .
EXPOSE      7001

# ENTRYPOINT [ "dockerize", "-wait", "tcp://$SQL_HOST:$SQL_PORT", "-timeout", "60s" ]
CMD [ "make", "run"]

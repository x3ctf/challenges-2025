FROM python:3.12-alpine

WORKDIR /app

RUN apk update --no-cache && apk upgrade --no-cache && apk add socat --no-cache

COPY chall.py /app

ENTRYPOINT socat tcp-l:1337,fork,reuseaddr exec:/app/chall.py
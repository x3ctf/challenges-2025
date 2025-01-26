FROM python:3.12-alpine

WORKDIR /app

RUN pip3 install pycryptodome
RUN apk update --no-cache && apk upgrade --no-cache && apk add socat cmake make git build-base --no-cache
RUN git clone https://github.com/wjakob/nanobind && cd nanobind && git checkout 0272db4cfd611902f8cdc534c545973642c1627f && git reset --hard && git submodule update --init --recursive

COPY SECRET.py /app
COPY chall.py /app
COPY Makefile /app
COPY CMakeLists.txt /app
COPY nttmul.cpp /app
COPY nttmul*.so /app

RUN make

ENTRYPOINT socat tcp-l:1337,fork,reuseaddr exec:/app/chall.py

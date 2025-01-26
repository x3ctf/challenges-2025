FROM ubuntu:22.04

RUN apt update && apt install -y socat

COPY pwny-heap /pwny-heap

COPY flag.txt /flag.txt

RUN chmod 555 /pwny-heap

ENTRYPOINT ["socat", "TCP-LISTEN:1337,reuseaddr,fork", "EXEC:\"./pwny-heap\""]

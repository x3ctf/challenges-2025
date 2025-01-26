FROM ubuntu:24.04

RUN apt update && apt install -y socat

WORKDIR /app/

COPY ./chall /app/chall
COPY ./flag /app/flag

RUN chown root:root /app/flag
RUN chown root:root /app/chall

RUN chmod 444 /app/flag
RUN chmod 555 /app/chall

ENTRYPOINT ["socat", "TCP-LISTEN:1337,reuseaddr,fork", "EXEC:\"./chall\""]

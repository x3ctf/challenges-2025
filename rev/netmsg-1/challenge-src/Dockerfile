FROM golang:1.23 AS builder

WORKDIR /
RUN mkdir /app/
ADD go.work /app/
ADD server /app/server/
ADD common /app/common/
ADD client /app/client/

RUN go build -C /app/server -tags netgo -o /server

FROM scratch
COPY --from=builder /server /server

EXPOSE 5001
USER 1000:1000

ENTRYPOINT ["/server"]

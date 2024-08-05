ARG APP_IMAGE=python:3.12-slim

FROM $APP_IMAGE AS base

FROM base as builder

RUN mkdir /install
WORKDIR /install

COPY requirements.txt /requirements.txt

RUN pip install --prefix=/install -r /requirements.txt

FROM base
ENV PORT 5051
WORKDIR /service
VOLUME [ "/data" ]
COPY --from=builder /install /usr/local
ADD . /service

EXPOSE 5051/tcp

ENTRYPOINT ["sh", "docker_init.sh"]
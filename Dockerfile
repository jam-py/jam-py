FROM python:3.8-slim

ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update && apt-get upgrade -y --no-install-recommends
RUN apt-get install -y --no-install-recommends git libreoffice

RUN git clone https://github.com/jam-py/jam-py.git /opt/jam-py
WORKDIR /opt/jam-py
RUN pip install .

# RUN pip install jam.py==5.4.136
# RUN mkdir -p /opt/jam-py
# COPY demo /opt/jam-py/demo

ENV PORT 8080
ENV LOG_LEVEL info

# remove debian stuff
RUN apt-get autoremove -y && \
    rm -rf /var/cache/apt/archives /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN useradd -ms /bin/bash -d /app jampy

COPY entrypoint.sh /opt/entrypoint.sh
RUN chmod u+x /opt/entrypoint.sh
ENTRYPOINT "/opt/entrypoint.sh"

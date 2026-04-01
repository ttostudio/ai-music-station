FROM savonet/liquidsoap:v2.3.2

USER root

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl python3 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY entrypoint.sh /entrypoint.sh
COPY silence.wav /etc/liquidsoap/silence.wav

RUN chmod +x /entrypoint.sh

USER liquidsoap

ENTRYPOINT ["/entrypoint.sh"]

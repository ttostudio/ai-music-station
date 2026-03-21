FROM savonet/liquidsoap:v2.3.2

USER root

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY entrypoint.sh /entrypoint.sh
COPY channel.liq /etc/liquidsoap/channel.liq
COPY silence.wav /tmp/silence.wav
RUN ffmpeg -i /tmp/silence.wav -c:a flac /etc/liquidsoap/silence.flac -y && rm /tmp/silence.wav

RUN chmod +x /entrypoint.sh

USER liquidsoap

ENTRYPOINT ["/entrypoint.sh"]

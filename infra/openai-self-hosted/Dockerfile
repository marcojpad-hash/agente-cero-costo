FROM node:22-bookworm-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates git openssh-client python3 \
 && rm -rf /var/lib/apt/lists/* \
 && npm install --global @openai/codex@alpha \
 && useradd --create-home --uid 10001 --shell /usr/sbin/nologin codex \
 && mkdir -p /workspace \
 && chown -R codex:codex /workspace /home/codex

WORKDIR /workspace
COPY --chmod=0755 entrypoint.sh /usr/local/bin/entrypoint.sh
USER 10001:10001
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

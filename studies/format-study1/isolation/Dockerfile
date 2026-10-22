FROM node:24.19.0-bookworm-slim@sha256:a9f5f7c91a432850b2a8a7797adf5eadb6c733ceed61167806cee7ea7fbc29df
RUN npm install --global @openai/codex@0.157.1 && npm cache clean --force
COPY client.mjs relay.mjs live_transport.mjs /opt/isolation/
USER 65534:65534
WORKDIR /tmp
ENTRYPOINT ["node", "/opt/isolation/client.mjs"]

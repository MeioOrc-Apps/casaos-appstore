FROM alpine:3.21

ARG TARGETARCH

RUN apk add --no-cache \
      curl \
      bash \
      ca-certificates \
      dcron \
      tzdata \
      docker-cli

# CronitorCLI arch-aware install.
# Validates binary name inside tarball empirically; may need adjustment for arm64 tarball layout.
RUN set -eux; \
    case "${TARGETARCH:-amd64}" in \
      amd64) CRON_ARCH="linux_amd64" ;; \
      arm64) CRON_ARCH="linux_arm64" ;; \
      *) echo "unsupported arch: ${TARGETARCH}" >&2; exit 1 ;; \
    esac; \
    curl -fsSL "https://cronitor.io/dl/${CRON_ARCH}.tar.gz" -o /tmp/cronitor.tar.gz; \
    tar -xzf /tmp/cronitor.tar.gz -C /usr/local/bin/; \
    chmod +x /usr/local/bin/cronitor; \
    rm /tmp/cronitor.tar.gz; \
    cronitor 2>&1 | head -1

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

EXPOSE 9000
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

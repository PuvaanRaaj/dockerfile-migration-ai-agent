# syntax=docker/dockerfile:1.7

FROM alpine:3.23  AS builder

ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    TZ=Asia/Kuala_Lumpur

RUN --mount=type=cache,target=/var/cache/apk \
    apk update && \
    apk add \
        openssh \
        tzdata \
        bash \
        vim \
        mlocate \
        chrony \
        zip \
        unzip \
        postfix \
        joe \
        busybox-extras \
        coreutils \
        findutils \
        ncurses \
        dnsmasq \
    && cp /usr/share/zoneinfo/${TZ} /etc/localtime \
    && echo "${TZ}" > /etc/timezone

# Upgrade vim from Alpine edge repository to fix CVE-2025-66476
RUN --mount=type=cache,target=/var/cache/apk \
    apk upgrade --repository=https://dl-cdn.alpinelinux.org/alpine/edge/community vim

# Build and install curl >= 8.18.0 from source to fix CVEs: CVE-2025-15079, CVE-2025-14819, CVE-2025-14524, CVE-2025-14017, CVE-2025-13034, CVE-2025-15224
# Alpine 3.23 only has curl 8.17.0, so we need to build from source
RUN --mount=type=cache,target=/var/cache/apk \
    apk add --virtual .build-deps \
        build-base \
        openssl-dev \
        nghttp2-dev \
        zlib-dev \
        libpsl-dev \
        ca-certificates \
        wget \
    && CURL_VERSION="8.18.0" \
    && cd /tmp \
    && wget -q "https://curl.se/download/curl-${CURL_VERSION}.tar.gz" \
    && tar -xzf "curl-${CURL_VERSION}.tar.gz" \
    && cd "curl-${CURL_VERSION}" \
    && ./configure \
        --prefix=/usr \
        --with-openssl \
        --with-nghttp2 \
        --with-zlib \
        --disable-dependency-tracking \
        --disable-static \
        --enable-shared \
    && make -j$(nproc) \
    && make install \
    && apk del .build-deps

COPY etc/bashrc /etc/bashrc
COPY .bashrc /root/.bashrc
COPY etc/postfix/main.cf /etc/postfix/main.cf
COPY etc/postfix/master.cf /etc/postfix/master.cf
COPY etc/postfix/postfix.sh /etc/postfix/postfix.sh

# dnsmasq config files
COPY etc/dnsmasq/dnsmasq.conf /etc/dnsmasq.conf
COPY etc/dnsmasq/update_dnsmasq_upstream.sh /etc/dnsmasq/update_dnsmasq_upstream.sh
# Leave upstream list empty for now; we'll generate it at runtime
RUN touch /etc/dnsmasq.upstream.conf && chmod +x /etc/dnsmasq/update_dnsmasq_upstream.sh

FROM builder AS final
# optional: remove leftover temp files
RUN rm -rf /tmp/* /var/tmp/* /var/cache/apk/*

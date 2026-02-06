# syntax=docker/dockerfile:1.7

# Use the official Debian base image
FROM debian:12.9 AS builder

# Set environment variables to avoid interactive prompts and set default values
ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8

# Set the timezone to Asia/Kuala_Lumpur, and install required packages
ENV TZ=Asia/Kuala_Lumpur
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && \
    echo $TZ > /etc/timezone

RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/var/lib/apt \
    apt-get update && apt-get upgrade -y && \
    apt-get install --no-install-recommends -y \
    curl \
    bash \
    ssh \
    vim \
    mlocate \
    chrony \
    zip \
    unzip \
    postfix \
    joe \
    telnet \
    software-properties-common \
    dnsmasq

# Copy the contents of these files from the repo to the actual path in the container
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

# |--------------------------------------------|
# | Cleaning - Reducing Space                  |
# |--------------------------------------------|

RUN apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

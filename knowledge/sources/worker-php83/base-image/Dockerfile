# syntax=docker/dockerfile:1.7
# |--------------------------------------------|
# | From Golden Image                          |
# |--------------------------------------------|

ARG IMAGE_VERSION="null"
ARG CI_REGISTRY="null"

# To run localhost make sure use latest tag
FROM ${CI_REGISTRY}/server/golden-images/alpine:${IMAGE_VERSION} AS builder

# |--------------------------------------------|
# | Install package and dependencies           |
# |--------------------------------------------|

# Update package list and install common utilities
RUN --mount=type=cache,target=/var/cache/apk \
    apk update \
    && apk upgrade \
    && apk add \
    git \
    ca-certificates \
    openssh-client \
    g++ \
    make

# Install required library below for PHP extensions
RUN --mount=type=cache,target=/var/cache/apk \
    apk add \
    libpng-dev \
    gmp-dev \
    imap-dev \
    icu-dev \
    openldap-dev \
    libxml2-dev \
    tidyhtml-dev \
    libzip-dev \
    net-snmp-dev

# |--------------------------------------------|
# | Install PHP                                |
# |--------------------------------------------|

# Add repository
RUN echo "https://dl-cdn.alpinelinux.org/alpine/v3.22/main/" >> /etc/apk/repositories
RUN echo "http://dl-cdn.alpinelinux.org/alpine/edge/main" >> /etc/apk/repositories
RUN echo "http://dl-cdn.alpinelinux.org/alpine/edge/community" >> /etc/apk/repositories
RUN echo "http://dl-cdn.alpinelinux.org/alpine/edge/testing" >> /etc/apk/repositories

RUN --mount=type=cache,target=/var/cache/apk \
    apk add --virtual \
    .build-php $PHPIZE_DEPS \
    gearman-dev \
    imagemagick-dev \
    libmemcached-dev \
    pcre-dev \
    libssh2-dev \
    yaml-dev \
    hiredis-dev

# Install required packages and PHP CLI
RUN --mount=type=cache,target=/var/cache/apk \
    apk add \
    php83 \
    php83-ctype \ 
    php83-curl \
    php83-dom \
    php83-fileinfo \
    php83-ftp \
    php83-iconv \ 
    php83-json \
    php83-mbstring \
    php83-openssl \
    php83-pdo \
    php83-pdo_sqlite \
    php83-phar \
    php83-posix \
    php83-session \
    php83-simplexml \
    php83-sqlite3 \
    php83-tokenizer \
    php83-xml \
    php83-sockets \
    php83-xmlreader \
    php83-xmlwriter \
    php83-sodium \
    php83-mysqlnd \
    php83-bcmath \
    php83-dba \
    php83-gd \
    php83-gmp \
    php83-imap \
    php83-intl \
    php83-ldap \
    php83-opcache  \
    php83-soap \
    php83-tidy \
    php83-zip \
    php83-bz2 \
    php83-snmp \
    php83-mysqli \
    php83-pear \
    php83-dev

# Create php symlink for scripts expecting 'php' command
RUN ln -sf /usr/bin/php83 /usr/bin/php

# pecl - Try to install redis via package first, fallback to pecl83
RUN --mount=type=cache,target=/var/cache/apk \
    apk add --virtual \
    php83-pecl-apcu \
    php83-pecl-igbinary \
    php83-pecl-imagick-dev \
    php83-pecl-memcached \
    php83-pecl-oauth \
    php83-pecl-ssh2 \
    php83-pecl-yaml \
    && (apk add php83-pecl-msgpack 2>/dev/null || echo "php83-pecl-msgpack not available, will install via pecl") \
    && (apk add php83-pecl-redis 2>/dev/null || echo "php83-pecl-redis not available, will use pecl83") \
    && PECL=$(command -v pecl83 2>/dev/null || command -v pecl 2>/dev/null || echo /usr/bin/pecl83) \
    && if [ -x "$PECL" ] || [ -f "$PECL" ]; then \
        $PECL channel-update pecl.php.net || true; \
        $PECL install gearman uuid; \
        if ! apk info -e php83-pecl-msgpack >/dev/null 2>&1; then \
            echo "Installing msgpack via pecl (required by redis)..." && \
            $PECL install msgpack; \
        fi; \
        if ! apk info -e php83-pecl-redis >/dev/null 2>&1; then \
            echo "Installing redis via pecl..." && \
            $PECL install redis; \
        fi; \
    else \
        echo "ERROR: pecl83 not found. Checking installation..." && \
        ls -la /usr/bin/pecl* /usr/local/bin/pecl* 2>/dev/null || true && \
        find /usr -name pecl* -type f 2>/dev/null | head -5 && \
        echo "Please ensure php83-pear is installed correctly." && exit 1; \
    fi

# |--------------------------------------------|
# | Install NewRelic Agent                     |
# |--------------------------------------------|

# Install New Relic PHP agent from local tar.gz file
# Version: 12.4.0.29 - see https://github.com/newrelic/newrelic-php-agent/releases
COPY core/newrelic/newrelic-php5-12.4.0.29-linux-musl.tar.gz /tmp/newrelic.tar.gz
RUN echo "Installing NewRelic PHP agent version 12.4.0.29..." && \
    echo "Extracting NewRelic agent..." && \
    tar -xvzf /tmp/newrelic.tar.gz -C /tmp && \
    mv /tmp/newrelic-php5-*/ /tmp/newrelic && \
    echo "Installing NewRelic agent..." && \
    export NR_INSTALL_SILENT=1 && \
    export NR_INSTALL_DAEMON=0 && \
    export PATH="/usr/bin:$PATH" && \
    PHP_VERSION=$(php83 -r 'echo PHP_MAJOR_VERSION.".".PHP_MINOR_VERSION;' 2>/dev/null || php -r 'echo PHP_MAJOR_VERSION.".".PHP_MINOR_VERSION;' 2>/dev/null || echo "83") && \
    echo "Detected PHP version: $PHP_VERSION" && \
    EXT_DIR=$(php83 -r 'echo ini_get("extension_dir");' || php -r 'echo ini_get("extension_dir");') && \
    echo "Extension directory: $EXT_DIR" && \
    echo "Detecting system architecture..." && \
    ARCH=$(uname -m) && \
    echo "Architecture: $ARCH" && \
    if [ "$ARCH" = "x86_64" ]; then \
        ARCH_DIR="x64"; \
    elif [ "$ARCH" = "aarch64" ] || [ "$ARCH" = "arm64" ]; then \
        ARCH_DIR="aarch64"; \
    else \
        ARCH_DIR="x64"; \
        echo "Unknown architecture $ARCH, defaulting to x64"; \
    fi && \
    echo "Looking for PHP 8.3 compatible NewRelic binary (module API 20230831)..." && \
    echo "Searching in agent/$ARCH_DIR..." && \
    NEWRELIC_SO=$(find /tmp/newrelic/agent/$ARCH_DIR -name "*20230831*.so" -type f 2>/dev/null | head -1) && \
    if [ -z "$NEWRELIC_SO" ] || [ ! -f "$NEWRELIC_SO" ]; then \
        echo "PHP 8.3 binary (20230831) not found, trying alternative names..." && \
        NEWRELIC_SO=$(find /tmp/newrelic/agent/$ARCH_DIR -name "newrelic-*.so" -type f 2>/dev/null | grep -i "20230831" | head -1); \
    fi && \
    if [ -z "$NEWRELIC_SO" ] || [ ! -f "$NEWRELIC_SO" ]; then \
        echo "Listing all available binaries in agent/$ARCH_DIR:" && \
        find /tmp/newrelic/agent/$ARCH_DIR -name "*.so" -type f 2>/dev/null && \
        echo "Trying to find binary with highest module API version (should be 20230831 for PHP 8.3)..." && \
        NEWRELIC_SO=$(find /tmp/newrelic/agent/$ARCH_DIR -name "newrelic-*.so" -type f 2>/dev/null | sort -V | tail -1); \
    fi && \
    if [ -z "$NEWRELIC_SO" ] || [ ! -f "$NEWRELIC_SO" ]; then \
        echo "ERROR: NewRelic PHP agent binary not found in architecture directory agent/$ARCH_DIR (arch: $ARCH). Refusing to use other architectures to avoid wrong-architecture binary." && \
        echo "Contents of /tmp/newrelic/agent/$ARCH_DIR:" && \
        (find /tmp/newrelic/agent/$ARCH_DIR -type f -name "*.so" 2>/dev/null || echo "(none or directory missing)") && \
        exit 1; \
    fi && \
    echo "Found NewRelic .so file: $NEWRELIC_SO" && \
    echo "Copying to extension directory..." && \
    cp "$NEWRELIC_SO" "$EXT_DIR/newrelic.so" && \
    echo "NewRelic extension installed successfully at $EXT_DIR/newrelic.so" && \
    echo "Cleaning up temporary files..." && \
    rm -rf /tmp/newrelic* /tmp/newrelic.tar.gz

# |--------------------------------------------|
# | Install Supervisord                        |
# |--------------------------------------------|

RUN --mount=type=cache,target=/var/cache/apk \
    apk add supervisor

# |--------------------------------------------|
# | Initialize                                 |
# |--------------------------------------------|
    
# PHP custom config - nc (no comment)
COPY core/php/conf.d/*  /etc/php83/conf.d/
COPY core/php/php.ini /etc/php83/php.ini
RUN grep -vE '^\s*[#;]|^$' /etc/php83/php.ini | sed 's/^\s\+//' > /etc/php83/php-nc.ini
RUN mv /etc/php83/php-nc.ini /etc/php83/php.ini
COPY core/newrelic/newrelic.ini.template /etc/php83/conf.d/newrelic.ini

# Supervisor custom config
COPY core/supervisor/supervisord.conf /etc/supervisord.conf 

# Bashrc custom config
COPY core/bash/.bashrc /root/.bashrc

# composer custom config
COPY core/composer/composer-v2.6.5.phar /usr/local/bin/composer
RUN chmod +x /usr/local/bin/composer

# check user apache if have, if not add user
# RUN id apache 2>/dev/null || adduser -S -D -H -G www-data apache

# Copy entrypoint script and give file permission
COPY core/scripts/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Final stage: copy from builder and clean up
FROM builder AS final

# |--------------------------------------------|
# | Cleaning - Reducing Space                  |
# |--------------------------------------------|

RUN apk cache clean \
    && rm -rf /tmp/* /var/tmp/* /root/.pearlogs /var/cache/apk/* /var/lib/apt/lists/*

# |--------------------------------------------|
# | start                                      |
# |--------------------------------------------|

# RUN script at entrypoint
CMD ["/bin/bash", "/entrypoint.sh"]

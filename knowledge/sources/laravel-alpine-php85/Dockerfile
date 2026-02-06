# syntax=docker/dockerfile:1.7

# |--------------------------------------------|
# | Args                                       |
# |--------------------------------------------|
ARG IMAGE_VERSION="null"
ARG CI_REGISTRY="null"

# |--------------------------------------------|
# | Builder Stage (build tools + runtime)      |
# |--------------------------------------------|
FROM ${CI_REGISTRY}/server/golden-images/alpine:${IMAGE_VERSION} AS builder
ARG TARGETARCH

# Base + build deps
RUN --mount=type=cache,id=apk-${TARGETARCH},target=/var/cache/apk \
    apk update && apk upgrade && apk add \
    git \
    openssl \
    openssh-client \
    supervisor \
    nginx \
    nginx-mod-http-headers-more \
    sqlite \
    libpq \
    libpng-dev \
    libjpeg-turbo-dev \
    freetype-dev \
    libzip-dev \
    zlib-dev \
    icu-dev \
    curl-dev \
    lz4-dev \
    build-base \
    linux-headers \
    ca-certificates \
    shadow \
    autoconf \
    vim \
    && (getent group www-data || addgroup -g 1000 www-data) \
    && (getent passwd www-data || adduser -u 1000 -G www-data -s /bin/sh -D www-data) \
    && mkdir -p /var/www \
    && chown -R www-data:www-data /var/www

# Vim config - disable mouse visual mode for normal copy/paste
RUN echo "set mouse-=a" > /root/.vimrc

# PHP & extensions
RUN --mount=type=cache,id=apk-${TARGETARCH},target=/var/cache/apk \
    apk add --update-cache \
    php85 \
    php85-cli \
    php85-fpm \
    php85-curl \
    php85-gd \
    php85-pdo_mysql \
    php85-mbstring \
    php85-mysqli \
    php85-pgsql \
    php85-xml \
    php85-zip \
    php85-intl \
    php85-sqlite3 \
    php85-pdo_sqlite \
    php85-sockets \
    php85-redis \
    php85-pear \
    php85-dev \
    php85-phar \
    php85-openssl \
    php85-tokenizer \
    php85-ctype \
    php85-fileinfo \
    php85-iconv \
    php85-dom \
    php85-session \
    php85-xmlwriter \
    php85-xmlreader \
    php85-simplexml \
    php85-bcmath \
    php85-pecl-igbinary \
    php85-pecl-msgpack

# PHP tool symlinks
RUN ln -sf /usr/bin/pecl85 /usr/bin/pecl \
    && ln -sf /usr/bin/phpize85 /usr/bin/phpize \
    && ln -sf /usr/bin/php-config85 /usr/bin/php-config \
    && ln -sf /usr/bin/php85 /usr/bin/php \
    && ln -sf /usr/sbin/php-fpm85 /usr/sbin/php-fpm \
    && mkdir -p /usr/local/sbin \
    && ln -sf /usr/sbin/php-fpm85 /usr/local/sbin/php-fpm

# PECL extensions (inotify)
RUN pecl channel-update pecl.php.net \
    && yes '' | pecl install inotify \
    && echo "extension=inotify.so" > /etc/php85/conf.d/20_inotify.ini

# Install Swoole from source for PHP 8.5 support
RUN apk add --no-cache git \
    && cd /tmp \
    && git clone --depth 1 https://github.com/swoole/swoole-src.git \
    && cd swoole-src \
    && phpize \
    && ./configure --enable-openssl --enable-sockets --enable-mysqlnd \
    && make -j$(nproc) \
    && make install \
    && echo "extension=swoole.so" > /etc/php85/conf.d/20_swoole.ini \
    && cd / \
    && rm -rf /tmp/swoole-src


# Copy New Relic tar file and install the agent.
# NOTE: PHP 8.5 uses Zend API 20250101 (or similar). The New Relic agent must
# be compatible with this version. If no compatible agent is found, we skip
# the New Relic installation to avoid runtime errors.
COPY core/newrelic/newrelic-php5-11.9.0.23-linux.tar.gz /tmp/newrelic.tar.gz
COPY core/newrelic/newrelic.ini.template /tmp/newrelic.ini.template

# Get PHP's Zend API version and attempt to find matching New Relic agent
RUN tar -xvzf /tmp/newrelic.tar.gz -C /tmp && \
    mv /tmp/newrelic-php5-*/ /tmp/newrelic && \
    export NR_INSTALL_SILENT=1 && \
    export NR_INSTALL_DAEMON=0 && \
    # Get the Zend API version from PHP
    ZEND_API=$(php -i | grep 'PHP Extension =>' | awk '{print $4}') && \
    EXT_DIR=$(php -i | grep extension_dir | awk '{print $3}' | head -n1) && \
    echo "PHP Zend Extension Build: $ZEND_API" && \
    echo "PHP Extension Directory: $EXT_DIR" && \
    # Try to find matching New Relic agent
    if [ -f "/tmp/newrelic/agent/x64/newrelic-${ZEND_API}.so" ]; then \
        echo "Found matching New Relic agent for Zend API $ZEND_API"; \
        cp "/tmp/newrelic/agent/x64/newrelic-${ZEND_API}.so" "$EXT_DIR/newrelic.so"; \
        cp /tmp/newrelic.ini.template /etc/php85/conf.d/newrelic.ini; \
    else \
        echo "WARNING: No compatible New Relic agent found for PHP 8.5 (Zend API $ZEND_API)"; \
        echo "Available agents:"; \
        ls -la /tmp/newrelic/agent/x64/*.so 2>/dev/null || echo "No agents found"; \
        echo "New Relic will be disabled - ini file not copied."; \
    fi && \
    rm -rf /tmp/newrelic.tar.gz /tmp/newrelic /tmp/newrelic.ini.template

# Composer
# COPY --from=composer:2.9.5 --chmod=0755 /usr/bin/composer /usr/bin/composer

# Copy Composer executable
COPY core/composer-2.9.5 /usr/local/bin/composer
RUN chmod +x /usr/local/bin/composer

# |--------------------------------------------|
# | Final Stage (use builder as final)         |
# |--------------------------------------------|
FROM builder AS final

# Config files
COPY core/php.ini /etc/php85/php.ini
COPY core/www.conf /etc/php85/php-fpm.d/www.conf
COPY core/nginx.conf /etc/nginx/nginx.conf
COPY core/app.conf /etc/nginx/conf.d/app.conf
COPY core/supervisord.conf /etc/supervisord.conf
COPY certs/cert.pem /etc/pki/tls/certs/cert.pem
COPY certs/key.pem /etc/pki/tls/certs/key.pem

# Entrypoint
COPY core/docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

WORKDIR /var/www
EXPOSE 443

# Clean caches in final image
RUN apk cache clean \
    && rm -rf /tmp/* /var/tmp/* /root/.pearlogs /var/cache/apk/* /var/lib/apt/lists/*

# Create nginx temp dir after cleanup so it isn't removed
RUN mkdir -p /tmp/nginx_temp/client_body \
    && chown -R www-data:www-data /tmp/nginx_temp/ \
    && chmod -R 700 /tmp/nginx_temp/

CMD ["/bin/bash", "/entrypoint.sh"]

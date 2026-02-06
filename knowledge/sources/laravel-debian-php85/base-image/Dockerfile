# syntax=docker/dockerfile:1.7

# |--------------------------------------------|
# | Args                                       |
# |--------------------------------------------|
ARG IMAGE_VERSION="null"
ARG CI_REGISTRY="null"

# |--------------------------------------------|
# | Builder Stage (build tools + runtime)      |
# |--------------------------------------------|
FROM ${CI_REGISTRY}/server/golden-images/debian:${IMAGE_VERSION} AS builder

# |--------------------------------------------|
# | Install package and dependencies           |
# |--------------------------------------------|
RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/var/lib/apt \
    apt-get update \
    && apt-get -y upgrade \
    && apt-get -y install --no-install-recommends \
    net-tools \
    git \
    openssh-client \
    lsb-release \
    ca-certificates \
    curl \
    gnupg

# |--------------------------------------------|
# | Install Apache                             |
# |--------------------------------------------|
RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/var/lib/apt \
    apt-get update && apt-get -y install --no-install-recommends \
    apache2 \
    libapache2-mod-fcgid

# |--------------------------------------------|
# | Install PHP 8.5 & Modules                  |
# |--------------------------------------------|
RUN curl -sSLo /tmp/debsuryorg-archive-keyring.deb https://packages.sury.org/debsuryorg-archive-keyring.deb \
    && dpkg -i /tmp/debsuryorg-archive-keyring.deb \
    && sh -c 'echo "deb [signed-by=/usr/share/keyrings/deb.sury.org-php.gpg] https://packages.sury.org/php/ $(lsb_release -sc) main" > /etc/apt/sources.list.d/php.list' \
    && rm /tmp/debsuryorg-archive-keyring.deb

RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/var/lib/apt \
    apt-get update && apt-get -y install --no-install-recommends \
    php8.5 \
    php8.5-curl \
    php8.5-fpm \
    php8.5-gd \
    php8.5-mbstring \
    php8.5-mysql \
    php8.5-xml \
    php8.5-sockets

# PHP-FPM symlink
RUN ln -sf /usr/sbin/php-fpm8.5 /usr/sbin/php-fpm

# |--------------------------------------------|
# | Install NewRelic Agent                     |
# |--------------------------------------------|
# NOTE: PHP 8.5 uses a new Zend API. The New Relic agent must be compatible.
# If no compatible agent is found, New Relic is skipped to avoid runtime errors.
COPY core/newrelic/newrelic-php5-11.9.0.23-linux.tar.gz /tmp/newrelic.tar.gz

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
    else \
        echo "WARNING: No compatible New Relic agent found for PHP 8.5 (Zend API $ZEND_API)"; \
        echo "Available agents:"; \
        ls -la /tmp/newrelic/agent/x64/*.so 2>/dev/null || echo "No agents found"; \
        echo "New Relic will be disabled. Update the agent when PHP 8.5 support is available."; \
        touch "$EXT_DIR/.newrelic_disabled"; \
    fi && \
    rm -rf /tmp/newrelic.tar.gz /tmp/newrelic

# |--------------------------------------------|
# | Install Supervisor                         |
# |--------------------------------------------|
RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/var/lib/apt \
    apt-get update && apt-get install -y --no-install-recommends \
    supervisor

# |--------------------------------------------|
# | Composer                                   |
# |--------------------------------------------|
COPY --from=composer:2.9.2 --chmod=0755 /usr/bin/composer /usr/bin/composer

# |--------------------------------------------|
# | Final Stage                                |
# |--------------------------------------------|
FROM builder AS final

# |--------------------------------------------|
# | PHP Config                                 |
# |--------------------------------------------|
COPY core/php/php-fpm.d/www.conf /etc/php/8.5/fpm/pool.d/www.conf
COPY core/php/php-fpm.d/docker.conf /etc/php/8.5/fpm/pool.d/docker.conf
COPY core/php/conf.d/php-ini-overrides.ini /etc/php/8.5/fpm/conf.d/php-ini-overrides.ini
COPY core/php/conf.d/docker-fpm.ini /etc/php/8.5/fpm/conf.d/docker-fpm.ini
COPY core/newrelic/newrelic.ini.template /etc/php/8.5/cli/conf.d/newrelic.ini

# |--------------------------------------------|
# | Apache Config                              |
# |--------------------------------------------|
COPY core/apache2/ports.conf /etc/apache2/ports.conf
COPY core/apache2/conf-available/charset.conf /etc/apache2/conf-available/charset.conf
COPY core/apache2/conf-available/security.conf /etc/apache2/conf-available/security.conf
COPY core/apache2/sites-available/service_api.conf /etc/apache2/sites-available/service_api.conf
COPY core/apache2/mods-enabled/fcgid.conf /etc/apache2/mods-enabled/fcgid.conf

# Apache modules enable
RUN a2enmod \
    headers \
    ssl \
    proxy_fcgi \
    rewrite \
    mpm_event

# Apache site enable
RUN a2ensite service_api.conf

# |--------------------------------------------|
# | Supervisor Config                          |
# |--------------------------------------------|
COPY core/supervisor/supervisord.conf /etc/supervisor/supervisord.conf

# |--------------------------------------------|
# | Vim Config                                 |
# |--------------------------------------------|
COPY core/vimrc /etc/vim/vimrc.local

# |--------------------------------------------|
# | Entrypoint                                 |
# |--------------------------------------------|
COPY core/scripts/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# |--------------------------------------------|
# | Cleanup                                    |
# |--------------------------------------------|
RUN apt-get clean \
    && rm -rf /tmp/* /var/tmp/*

# |--------------------------------------------|
# | Start                                      |
# |--------------------------------------------|
WORKDIR /var/www

EXPOSE 443

CMD ["/bin/sh", "/entrypoint.sh"]

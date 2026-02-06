# Merchant Portal - API Server Base Image

## For testing purpose.

```sh
# remove comment
$ grep -vE '^\s*[#;]|^$' apache2.conf | sed 's/^\s\+//' > apache2-nc.conf

# docker
$ docker build --platform=linux/amd64 \
  --build-arg IMAGE_VERSION="latest" \
  --build-arg CI_REGISTRY="git2u.fiuu.com:4567" \
  -t mepo-api-base-image:latest .

$ docker run -d -p 443:443 \
  -e APACHE2_SUPERVISOR_AUTOSTART="true" \
  -e POSTFIX_SUPERVISOR_AUTOSTART="true" \
  mepo-api-base-image:latest

# check list of php
ls -l /usr/bin/php*
ls -l /usr/sbin/php-fpm*

# remove symlink
rm -f /usr/bin/php

# check version
$ python3 --version
--> Python 3.11.2

$ apache2 -v
--> Server version: Apache/2.4.62 (Debian)
--> Server built:   2024-10-04T15:21:08

$ supervisord --version
--> 4.2.5

$ php --version
--> PHP 8.5.1 (cli) (built: Dec 18 2025 20:05:39) (NTS)
--> Copyright (c) The PHP Group
--> Built by Debian
--> Zend Engine v4.5.1, Copyright (c) Zend Technologies
-->    with Zend OPcache v8.5.1, Copyright (c), by Zend Technologies

$ service php8.5-fpm status
--> php-fpm8.5 is running.

$ php-fpm -v
--> PHP 8.5.1 (fpm-fcgi) (built: Dec 18 2025 20:05:39) (NTS)
--> Copyright (c) The PHP Group
--> Built by Debian
--> Zend Engine v4.5.1, Copyright (c) Zend Technologies
-->   with Zend OPcache v8.5.1, Copyright (c), by Zend Technologies

$ postconf -d | grep '^mail_version'
--> mail_version = 3.7.11

$ postfix status
--> postfix/postfix-script: the Postfix mail system is running: PID: 411

$ composer --version
--> Composer version 2.9.2
--> PHP version 8.5.1 (/usr/bin/php8.5)
--> Run the "diagnose" command to get more detailed diagnostics output.
```

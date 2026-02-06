# MD SDK Base Image

[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat&logo=docker&logoColor=white)](https://docs.docker.com/)
[![PHP](https://img.shields.io/badge/PHP-8.4-777BB4?style=flat&logo=php&logoColor=white)](https://www.php.net/)
[![Nginx](https://img.shields.io/badge/Nginx-1.25-009639?style=flat&logo=nginx&logoColor=white)](https://nginx.org/)
[![Alpine](https://img.shields.io/badge/Alpine-Linux-0D597F?style=flat&logo=alpinelinux&logoColor=white)](https://alpinelinux.org/)

> Production-ready Docker base image for MD SDK applications, optimized for performance and security.

---

## ✨ Features

| Component      | Version | Description                         |
| -------------- | ------- | ----------------------------------- |
| **PHP**        | 8.4.x   | Latest PHP with FPM and extensions  |
| **Nginx**      | 1.25.x  | High-performance web server         |
| **Supervisor** | 4.2.x   | Process control for PHP-FPM & Nginx |
| **New Relic**  | 11.9.x  | Application performance monitoring  |
| **Composer**   | 2.8.8   | PHP dependency manager              |

### 🔌 PHP Extensions

<details>
<summary>Click to expand full extension list</summary>

| Extension | Extension  | Extension |
| --------- | ---------- | --------- |
| curl      | gd         | mbstring  |
| mysqli    | pdo_mysql  | pgsql     |
| xml       | zip        | intl      |
| sqlite3   | pdo_sqlite | sockets   |
| redis     | openssl    | json      |
| bcmath    | igbinary   | msgpack   |
| swoole    | inotify    | dom       |
| session   | tokenizer  | ctype     |

</details>

---

## 🚀 Quick Start

### Prerequisites

- Docker 20.10+ with BuildKit enabled
- Access to `git2u.fiuu.com:4567` container registry

### Build the Image

```bash
docker build --platform=linux/amd64 \
  --build-arg IMAGE_VERSION="latest" \
  --build-arg CI_REGISTRY="git2u.fiuu.com:4567" \
  -t md-sdk-image:latest .
```

### Verify Installation

```bash
# Start a container
docker run --rm -it md-sdk-image:latest /bin/sh

# Check versions
php --version     # PHP 8.4.x
nginx -v          # nginx/1.25.x
supervisord -v    # 4.2.x
```

---

## 📁 Project Structure

```
md-sdk/
├── Dockerfile              # Multi-stage build configuration
├── certs/                  # SSL certificates
│   ├── cert.pem
│   └── key.pem
└── core/                   # Configuration files
    ├── nginx.conf          # Main Nginx configuration
    ├── app.conf            # Nginx server block
    ├── php.ini             # PHP configuration
    ├── www.conf            # PHP-FPM pool configuration
    ├── supervisord.conf    # Process manager configuration
    ├── docker-entrypoint.sh
    └── newrelic/           # New Relic APM agent
```

---

## ⚙️ Configuration

### Environment Variables

| Variable        | Description              | Required |
| --------------- | ------------------------ | -------- |
| `IMAGE_VERSION` | Docker image version tag | Yes      |
| `CI_REGISTRY`   | Container registry URL   | Yes      |

### Ports

| Port | Protocol | Description         |
| ---- | -------- | ------------------- |
| 443  | HTTPS    | Nginx (TLS enabled) |
| 9000 | TCP      | PHP-FPM (internal)  |

---

## 🔒 Security

- TLS 1.2 enforced
- Security headers configured (HSTS, X-Frame-Options, X-Content-Type-Options)
- Server tokens disabled
- `.ht*` files blocked

---

## 📝 License

Proprietary - Fiuu © 2025

# Gearman Worker Base Image

A Docker base image for PHP-based Gearman workers in the Razer Merchant Services ecosystem. This image provides a complete runtime environment with PHP 8.3, Gearman support, NewRelic monitoring, and Supervisor process management.

## Overview

This base image is designed to serve as the foundation for Gearman worker applications that process background jobs in the merchant portal system. It includes all necessary dependencies, extensions, and configurations to run PHP-based worker processes efficiently.

## Features

### Core Components
- **PHP 8.3** with comprehensive extension support
- **Gearman Extension** for job queue processing
- **NewRelic APM** for application monitoring
- **Supervisor** for process management
- **Composer 2.6.5** for dependency management
- **Alpine Linux** base for minimal footprint

### PHP Extensions Included
- **Core Extensions**: ctype, curl, dom, fileinfo, json, mbstring, openssl, pdo, session, xml, etc.
- **Database**: mysqli, pdo_sqlite, mysqlnd
- **Utility**: bcmath, gd, gmp, imap, intl, ldap, opcache, soap, tidy, zip, bz2, snmp
- **PECL Extensions**: apcu, igbinary, imagick, memcached, oauth, ssh2, yaml, gearman, uuid, redis

### Monitoring & Management
- **NewRelic Integration**: Automatic configuration with environment variables
- **Supervisor Web Interface**: Available on port 9001 for process monitoring
- **Logging**: Structured logging to stdout for container environments

## Quick Start

### Building the Image

```bash
# Build with default settings
docker build -t gearman-worker-base .

# Build with custom registry and version
docker build \
  --build-arg CI_REGISTRY=your-registry.com \
  --build-arg IMAGE_VERSION=latest \
  -t gearman-worker-base .
```

### Running a Container

```bash
docker run -d \
  -e NEW_RELIC_LICENSE_KEY=your_license_key \
  -e NEW_RELIC_APP_NAME=your_app_name \
  -p 9001:9001 \
  gearman-worker-base
```

## Configuration

### Build Arguments

- `CI_REGISTRY`: Container registry URL
- `IMAGE_VERSION`: Base image version tag

> **Note**: NewRelic PHP agent version 12.4.0.29 is bundled locally in `core/newrelic/` and is not downloaded during build.

### Environment Variables

#### NewRelic Configuration (Required for AWS ECS)
- `NEW_RELIC_LICENSE_KEY`: Your NewRelic license key
- `NEW_RELIC_APP_NAME`: Application name for NewRelic monitoring
- `NEW_RELIC_DAEMON_ADDRESS`: (Optional) Custom daemon address

#### Supervisor Configuration
- `POSTFIX_SUPERVISOR_AUTOSTART`: Controls Postfix service autostart (default: true)

### Key Configuration Files

| File | Purpose |
|------|---------|
| `/etc/php83/php.ini` | Main PHP configuration |
| `/etc/php83/conf.d/03_gearman.ini` | Gearman extension configuration |
| `/etc/php83/conf.d/04_redis.ini` | Redis extension configuration |
| `/etc/php83/conf.d/newrelic.ini` | NewRelic configuration template |
| `/etc/supervisord.conf` | Supervisor process management |
| `/entrypoint.sh` | Container startup script |

## Usage in Applications

This base image is intended to be extended by application-specific Dockerfiles:

```dockerfile
FROM your-registry/gearman-worker-base:latest

# Copy your application code
COPY src/ /app/

# Install application dependencies
WORKDIR /app
RUN composer install --no-dev --optimize-autoloader

# Add supervisor configuration for your workers
COPY supervisor-workers.conf /etc/supervisord.d/

# Set working directory
WORKDIR /app
```

## Development

### Directory Structure

```
.
├── Dockerfile                          # Main Docker build file
├── core/
│   ├── bash/.bashrc                   # Custom bash configuration
│   ├── composer/composer-v2.6.5.phar  # Composer binary
│   ├── newrelic/
│   │   ├── newrelic-php5-12.4.0.29-linux.tar.gz  # NewRelic PHP agent
│   │   └── newrelic.ini.template                 # NewRelic configuration template
│   ├── php/
│   │   ├── conf.d/03_gearman.ini     # Gearman extension config
│   │   ├── conf.d/04_redis.ini       # Redis extension config
│   │   └── php.ini                   # Custom PHP configuration
│   ├── scripts/
│   │   ├── create-issue-notification.sh  # GitLab issue creation script
│   │   └── entrypoint.sh             # Container entry point
│   └── supervisor/
│       └── supervisord.conf          # Supervisor configuration
└── .gitlab-ci.yml                    # CI/CD pipeline configuration
```

### Building Locally

1. Ensure you have Docker installed
2. Clone this repository
3. Build the image:
   ```bash
   docker build -t gearman-worker-base .
   ```

### Testing

The image includes a streamlined CI/CD pipeline with:
- **Build Stage**: Builds the Docker image
- **Security Scanning**: Multi-architecture Grype vulnerability scanning for `amd64` and `arm64`
- **Production Notifications**: Issue notification creation for deployments

## CI/CD Pipeline

The project uses GitLab CI/CD with the following stages:

1. **Build**: Creates the Docker image
2. **Security**: Runs `grype_scan/amd64` and `grype_scan/arm64` using the shared `.grype_scan_multiarch` template
3. **Production**: Creates deployment/issue notifications

## Monitoring

### Supervisor Web Interface
Access the Supervisor web interface at `http://container-ip:9001` with:
- Username: `supervisor_admin`
- Password: `5up3rv1s0r_Adm1n`

### NewRelic Integration
The image automatically configures NewRelic when the required environment variables are provided. Monitor your Gearman workers through the NewRelic dashboard.

### Logging
All services log to stdout, making it compatible with container orchestration platforms like Docker Compose, Kubernetes, and AWS ECS.

## Security Considerations

- The image runs processes as root by default - consider using a non-root user for production
- Supervisor web interface is enabled - restrict access in production environments
- NewRelic configuration is handled via environment variables - use secure secret management
- Regular security updates are applied through the CI/CD pipeline

## Support

This base image is maintained by the Razer Merchant Services team. For issues or questions:

1. Check the GitLab CI/CD pipeline logs
2. Review the Supervisor logs via the web interface
3. Examine container logs: `docker logs <container-id>`

## Version History

The image follows semantic versioning and is automatically built from the main branch. Check the GitLab container registry for available versions.

## License

Internal use only - Razer Merchant Services

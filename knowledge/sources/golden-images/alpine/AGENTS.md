# AI Assistant Guide for Alpine Golden Image Repository

This document provides guidance for AI assistants working with this Docker golden image repository.

## Repository Overview

This repository contains a **Docker golden image** based on Alpine Linux 3.23. It serves as a base image for other server images in the Razer Merchant Services infrastructure, providing essential utilities, Postfix mail server, DNSmasq DNS caching, and GitLab CI/CD automation scripts.

## Key Components

### 1. Dockerfile Structure

- **Base Image**: `alpine:3.23`
- **Multi-stage Build**: Uses builder and final stages
- **Timezone**: Asia/Kuala_Lumpur (configured via `TZ` environment variable)
- **Locale**: UTF-8 (C.UTF-8)

### 2. Installed Packages

The image includes these essential packages:
- `openssh` - SSH server
- `tzdata` - Timezone data
- `curl` - HTTP client
- `bash` - Shell
- `vim`, `joe` - Text editors
- `mlocate` - File search
- `chrony` - NTP daemon
- `zip`, `unzip` - Archive utilities
- `postfix` - Mail server
- `busybox-extras`, `coreutils`, `findutils` - System utilities
- `ncurses` - Terminal control library
- `dnsmasq` - DNS/DHCP server

**When adding packages:**
- Use `apk add` with `--no-cache` flag when appropriate
- Group related packages together
- Keep the image size minimal
- Document new packages in README.md

### 3. Configuration Files

#### Postfix Configuration
- **Location**: `etc/postfix/`
- **Files**: `main.cf`, `master.cf`, `postfix.sh`
- **Runtime Configuration**: Postfix is configured at container startup via `postfix.sh` script
- **Environment Variables**:
  - `CONTAINER_HOSTNAME` - Mail server hostname
  - `MAIL_HOST` - Relay mail server hostname/IP
  - `MAIL_PORT` - Relay mail server port
  - `SYSADM_EMAIL` - Root email alias destination

#### DNSmasq Configuration
- **Location**: `etc/dnsmasq/`
- **Files**: `dnsmasq.conf`, `update_dnsmasq_upstream.sh`
- **Important**: The `update_dnsmasq_upstream.sh` script must be run at container entry in derived images
- **Runtime**: Creates `/etc/dnsmasq.upstream.conf` from `/etc/resolv.conf`

#### Bash Configuration
- **System-wide**: `etc/bashrc`
- **User-specific**: `.bashrc` (copied to `/root/.bashrc`)
- **Custom aliases**: `rm`, `cp`, `mv`, `ls`, `ll`, `j`, `tf`, `rscon`, `log`

### 4. GitLab CI/CD Pipeline

#### Pipeline Structure
- **Stages**: `build`, `security`, `push`, `production`
- **Multi-architecture**: Builds for `linux/amd64` and `linux/arm64`
- **Buildx**: Uses Docker buildx for multi-arch builds
- **Caching**: Registry cache with local cache fallback

#### Tagging Strategy
- **Main/Master branches**: `MajorVersion.MinorVersion.CI_JOB_ID-BASE_IMAGE_SANITIZED`
  - Example: `1.0.12345-alpine-3.23`
  - Base image extracted from Dockerfile `FROM` instruction
- **Other branches**: `CI_COMMIT_SHA` (full commit hash)

#### Security Scanning
- **Tool**: Grype
- **Platforms**: Separate scans for amd64 and arm64
- **Stage**: Runs after build, before production

### 5. Scripts

#### `etc/scripts/update-variables.sh`
- Updates GitLab CI/CD variables via API
- Reads from `variables.txt` file
- Triggers pipeline after updates

#### `etc/scripts/trigger_temp_pipeline.sh`
- Creates temporary pipeline trigger
- Triggers pipeline on specified branch
- Cleans up trigger after use

## Development Guidelines

### When Modifying the Dockerfile

1. **Maintain Multi-Architecture Support**
   - Test that packages work on both amd64 and arm64
   - Some packages may not be available for all architectures

2. **Layer Optimization**
   - Combine related `RUN` commands to reduce layers
   - Use `&&` to chain commands in single `RUN` statement
   - Clean up package cache: `apk del .build-deps` if used

3. **Security Best Practices**
   - Pin package versions when possible
   - Update base image regularly
   - Remove unnecessary packages
   - Use non-root user when possible (if applicable)

4. **Configuration File Changes**
   - Update corresponding documentation in README.md
   - Ensure runtime scripts handle new configurations
   - Test configuration changes in both architectures

### When Modifying CI/CD Pipeline

1. **Tagging Logic**
   - The tagging script extracts base image from Dockerfile
   - Ensure `FROM` instruction is parseable
   - Sanitization replaces `:` with `-` and `/` with `_`

2. **Buildx Configuration**
   - Builder name is unique per project and runner: `bx-${CI_PROJECT_ID}-${CI_RUNNER_ID}`
   - Uses local cache for faster builds
   - Registry cache export enabled

3. **Dependencies**
   - Security scans depend on build stage
   - Production stage depends on build completion

### When Adding New Features

1. **Documentation**
   - Update README.md with new features
   - Document environment variables
   - Provide usage examples

2. **Backward Compatibility**
   - Ensure existing derived images continue to work
   - Don't break existing configuration patterns
   - Consider versioning for breaking changes

3. **Testing**
   - Test on both amd64 and arm64 platforms
   - Verify Postfix and DNSmasq configurations
   - Test GitLab CI/CD pipeline changes

## Common Tasks

### Adding a New Package

```dockerfile
RUN apk add --no-cache \
    new-package \
    && rm -rf /var/cache/apk/*
```

### Updating Base Image Version

1. Update `FROM alpine:3.23` to new version
2. Test all functionality
3. Update README.md if version is mentioned
4. Tagging will automatically reflect new base image

### Modifying DNSmasq Configuration

1. Edit `etc/dnsmasq/dnsmasq.conf`
2. Test DNS resolution in derived images
3. Ensure `update_dnsmasq_upstream.sh` still works correctly

### Modifying Postfix Configuration

1. Edit files in `etc/postfix/`
2. Test mail relaying functionality
3. Verify environment variable handling in `postfix.sh`

## File Structure Conventions

```
alpine/
├── Dockerfile              # Main Dockerfile
├── .gitlab-ci.yml          # CI/CD pipeline configuration
├── .bashrc                 # Root user bash config
├── .dockerignore           # Docker ignore patterns
├── README.md               # User documentation
├── AGENTS.md               # This file (AI assistant guide)
└── etc/                    # Configuration files
    ├── bashrc              # System-wide bash config
    ├── dnsmasq/
    │   ├── dnsmasq.conf
    │   └── update_dnsmasq_upstream.sh
    ├── postfix/
    │   ├── main.cf
    │   ├── master.cf
    │   └── postfix.sh
    └── scripts/
        ├── update-variables.sh
        └── trigger_temp_pipeline.sh
```

## Important Notes

1. **DNSmasq Setup**: Derived images MUST run `/etc/dnsmasq/update_dnsmasq_upstream.sh` at container entry before starting applications.

2. **Postfix Configuration**: Postfix is configured at runtime, not build time. Environment variables must be set when running containers.

3. **Multi-Architecture**: Always consider both amd64 and arm64 when making changes. Some packages or configurations may differ between architectures.

4. **Tagging**: The CI/CD pipeline automatically generates tags based on branch and base image. Manual tagging is not required.

5. **Security**: Security scans run automatically in the pipeline. Address any vulnerabilities before merging to main/master.

## Questions to Consider

When making changes, consider:
- Does this work on both amd64 and arm64?
- Is the image size impact acceptable?
- Are configuration changes backward compatible?
- Is documentation updated?
- Are environment variables properly documented?
- Will derived images need updates?

## References

- [Alpine Linux Packages](https://pkgs.alpinelinux.org/packages)
- [Docker Multi-Architecture](https://docs.docker.com/build/building/multi-platform/)
- [Postfix Configuration](http://www.postfix.org/documentation.html)
- [DNSmasq Documentation](https://thekelleys.org.uk/dnsmasq/doc.html)
- [GitLab CI/CD](https://docs.gitlab.com/ee/ci/)

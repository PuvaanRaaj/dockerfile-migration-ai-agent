
# Alpine Base Image with Postfix and CI/CD Utilities

This repository contains a `Dockerfile` for building a customized Alpine Linux base image. This image is extended with essential utilities, a Postfix mail server, and custom scripts designed to facilitate CI/CD operations, particularly with GitLab.

> **Note for AI Assistants**: See [AGENTS.md](./AGENTS.md) for detailed guidance on working with this repository.

## Features

-   **Base Image**: Built on `alpine:3.23` for a lightweight and secure foundation.
-   **Essential Utilities**: Includes various packages for general system administration and debugging (see [Installed Packages](#installed-packages) below).
-   **Postfix Mail Server**: Configured for basic mail relaying with dynamic hostname and mail host/port configuration.
-   **DNSmasq DNS Caching**: Configured for DNS caching to improve DNS resolution performance and reduce external DNS queries.
-   **Custom Bash Configuration**: Enhances the user experience with custom `PS1` and useful aliases (`rm`, `cp`, `mv`, `ls`, `ll`, `j`, `tf`, `rscon`, `log`).
-   **GitLab CI/CD Integration**: Includes scripts to automate GitLab CI/CD variable updates and pipeline triggering.

## Installed Packages

The following packages are installed in this base image:

-   `openssh` - SSH server
-   `tzdata` - Timezone data
-   `curl` - HTTP client (version 8.18.0, built from source to address security vulnerabilities)
-   `bash` - Shell
-   `vim` - Editor (upgraded from Alpine edge repository)
-   `mlocate` - File search
-   `chrony` - NTP daemon
-   `zip` - Archive compression
-   `unzip` - Archive extraction
-   `postfix` - Mail server
-   `joe` - Text editor
-   `busybox-extras` - Additional busybox utilities
-   `coreutils` - Core GNU utilities
-   `findutils` - File search utilities
-   `ncurses` - Terminal control library
-   `dnsmasq` - DNS/DHCP server

### Special Package Handling

-   **curl**: Built from source (version 8.18.0) to address CVEs: CVE-2025-15079, CVE-2025-14819, CVE-2025-14524, CVE-2025-14017, CVE-2025-13034, and CVE-2025-15224. Alpine 3.23's repository only provides curl 8.17.0, so the image builds curl from source during the Docker build process.
-   **vim**: Upgraded from Alpine's edge repository to fix CVE-2025-66476 and ensure the latest version with security fixes.

## Building the Docker Image

### Local Build

To build the Docker image locally, navigate to the root of this repository and run the following command:

```bash
docker build -t your-image-name:tag .
```

Replace `your-image-name` and `tag` with your desired image name and tag.

### Multi-Architecture Build

This image is designed to support multiple architectures (amd64 and arm64). For local multi-arch builds, use Docker buildx:

```bash
docker buildx create --name multiarch --use
docker buildx build --platform linux/amd64,linux/arm64 -t your-image-name:tag .
```

The GitLab CI/CD pipeline automatically builds multi-architecture images for both platforms.

## Postfix Configuration

The Postfix mail server is configured during the container's startup via `etc/postfix/postfix.sh`. This script dynamically updates the `main.cf` configuration based on environment variables. The key parameters configured are:

-   `myhostname`: Set to `CONTAINER_HOSTNAME` environment variable.
-   `relayhost`: Set to `MAIL_HOST:MAIL_PORT` environment variables.
-   `root` alias: Configured to forward mail to the `SYSADM_EMAIL` environment variable.

### Environment Variables for Postfix

-   `CONTAINER_HOSTNAME`: The hostname for the mail server.
-   `MAIL_HOST`: The IP address or hostname of the relay mail server.
-   `MAIL_PORT`: The port of the relay mail server.
-   `SYSADM_EMAIL`: The email address where root-aliased mails should be sent.

## DNSmasq Configuration

The image includes a DNS caching server (`dnsmasq`) configured to cache DNS queries and improve DNS resolution performance. The configuration is located at `/etc/dnsmasq.conf`.

### DNSmasq Setup at Container Entry

**Important**: When using this image as a base for server images, you must run `/etc/dnsmasq/update_dnsmasq_upstream.sh` at container entry (e.g., in your Dockerfile `ENTRYPOINT` or startup script) before starting your application.

This script:
-   Captures upstream DNS resolvers from `/etc/resolv.conf` (excluding loopback addresses)
-   Creates `/etc/dnsmasq.upstream.conf` with the upstream nameservers
-   Updates `/etc/resolv.conf` to point to `127.0.0.1` (dnsmasq on localhost)
-   Falls back to public resolvers (1.1.1.1, 8.8.8.8) if no upstream resolvers are found

**Example usage in a server image Dockerfile:**

```dockerfile
FROM your-base-image:tag

# Your application setup...

# Create entrypoint script
RUN echo '#!/bin/sh' > /entrypoint.sh && \
    echo '/etc/dnsmasq/update_dnsmasq_upstream.sh' >> /entrypoint.sh && \
    echo 'dnsmasq' >> /entrypoint.sh && \
    echo 'exec "$@"' >> /entrypoint.sh && \
    chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["your-app"]
```

Or in a startup script:

```bash
#!/bin/sh
/etc/dnsmasq/update_dnsmasq_upstream.sh
dnsmasq
exec "$@"
```

## GitLab CI/CD Scripts

This repository includes two utility scripts located in `etc/scripts/`:

### `etc/scripts/update-variables.sh`

This script is designed to update or create CI/CD variables in GitLab projects. It reads variable definitions from a `variables.txt` file and uses the GitLab API to manage them.

**Usage:**

```bash
./etc/scripts/update-variables.sh
```

**Dependencies:**

-   `variables.txt`: A file in the root of the repository that defines the CI/CD variables to be managed. Each line should follow the format: `PROJECT_PATH|KEY|VALUE|PROTECTED|MASKED`.
    -   `PROJECT_PATH` must be URL-encoded (e.g., `mygroup%2Fmyproject`).
    -   `PROTECTED` and `MASKED` should be `true` or `false`.
-   `CI_API_V4_URL`: GitLab API URL (usually provided by GitLab CI/CD).
-   `ACCESS_TOKEN`: A GitLab private token with appropriate permissions to manage project variables.
-   `TARGET_BRANCH`: (Optional) The branch to trigger the pipeline on after updating variables (defaults to `main`).

### `etc/scripts/trigger_temp_pipeline.sh`

This script creates a temporary pipeline trigger in a specified GitLab project, triggers a pipeline on a given branch, and then cleans up the temporary trigger. It is primarily called by `update-variables.sh` after a variable update.

**Usage:** (Typically called internally by `update-variables.sh`)

```bash
./etc/scripts/trigger_temp_pipeline.sh
```

**Dependencies:**

-   `ACCESS_TOKEN`: GitLab private token.
-   `GITLAB_API`: GitLab API URL.
-   `TARGET_PROJECT_PATH`: The path of the target GitLab project (e.g., `mygroup/myproject`).
-   `TARGET_BRANCH`: The branch to trigger the pipeline on (defaults to `main`).

## GitLab CI/CD Build Process

This repository includes a `.gitlab-ci.yml` file that defines the CI/CD pipeline for building and managing this Docker image.

### Pipeline Stages

The pipeline consists of four stages:
1. **build**: Builds multi-architecture Docker images (amd64 and arm64)
2. **security**: Runs Grype vulnerability scans on both architectures
3. **push**: Pushes images to the container registry
4. **production**: Updates image tags in production configuration

### Tagging Strategy

The `build` stage includes dynamic tagging logic:

-   **Tagging for `master` or `main` branches**: If the commit is on the `master` or `main` branch, the `CI_APPLICATION_TAG` is composed using `MajorVersion.MinorVersion.CI_JOB_ID-BASE_IMAGE_SANITIZED`. The `BASE_IMAGE_SANITIZED` is extracted from the `Dockerfile`'s `FROM` instruction (e.g., `alpine-3.23` from `alpine:3.23`).
    -   Example: `1.0.12345-alpine-3.23`
    -   Main/master builds are also pushed with the `latest` tag (e.g., `$CI_REGISTRY_IMAGE:latest`).
-   **Tagging for other branches**: For any other branch, the `CI_APPLICATION_TAG` is set to the full `CI_COMMIT_SHA`. The `latest` tag is not pushed for non-main branches.

This ensures that main branch builds are tagged with a human-readable and version-specific tag plus `latest`, while other branches use only the commit SHA for unique identification.

### Multi-Architecture Support

The build process automatically creates images for both `linux/amd64` and `linux/arm64` platforms using Docker buildx. Both architectures are built, scanned for security vulnerabilities, and pushed to the registry.

### Running the Docker Image

You can run the built Docker image and expose the Postfix SMTP port (25) as follows:

```bash
docker run -d \
  -p 25:25 \
  -e CONTAINER_HOSTNAME="your.mailserver.com" \
  -e MAIL_HOST="smtp.yourprovider.com" \
  -e MAIL_PORT="587" \
  -e SYSADM_EMAIL="admin@yourdomain.com" \
  your-image-name:tag
```

Replace the environment variable values with your actual mail server details and administrator email.

## Using as a Base Image

You can extend this Alpine base image in your own `Dockerfile`s. For example:

```dockerfile
FROM your-image-name:tag

# Install additional packages
RUN apk add --no-cache nginx

# Copy your application files
COPY . /app

# Set working directory
WORKDIR /app

# Define default command
CMD ["nginx", "-g", "daemon off;"]
```

Replace `your-image-name:tag` with the actual name and tag of the image you built from this repository.

## Directory Structure

```
alpine/
  - Dockerfile
  - .gitlab-ci.yml
  - .bashrc
  - .dockerignore
  - AGENTS.md              # AI assistant guide
  - README.md              # This file
  - etc/
    - bashrc
    - dnsmasq/
      - dnsmasq.conf
      - update_dnsmasq_upstream.sh
    - postfix/
      - main.cf
      - master.cf
      - postfix.sh
    - scripts/
      - trigger_temp_pipeline.sh
      - update-variables.sh
```

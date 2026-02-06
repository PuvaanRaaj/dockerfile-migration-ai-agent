# Debian Golden Image

This repository contains the Dockerfile and associated configuration files for building a Debian 12.9 golden image. This image serves as a standardized base for various services, ensuring a consistent and pre-configured environment.

## Features

The golden image includes the following key features and pre-installed packages:

*   **Base Image:** Debian 12.9
*   **Timezone:** Configured to `Asia/Kuala_Lumpur`
*   **Essential Utilities:**
    *   `curl`: Transfer data with URLs
    *   `bash`: GNU Bourne-Again Shell
    *   `ssh`: Secure Shell client
    *   `vim`: Vi IMproved - enhanced vi editor
    *   `mlocate`: Quickly find files by name
    *   `chrony`: NTP client and server
    *   `zip`/`unzip`: Archive utilities
    *   `joe`: Joe's Own Editor
    *   `telnet`: User interface to the TELNET protocol
    *   `software-properties-common`: Manage your distribution and independent software vendor software sources
    *   `dnsmasq`: Lightweight DNS forwarder and DHCP server
*   **Mail Transfer Agent (MTA):** Postfix is installed and configured.

## Directory Structure

*   `/`: Root directory of the repository.
*   `Dockerfile`: Defines the steps to build the Debian golden image.
*   `etc/`: Contains configuration files and scripts.
    *   `bashrc`: Global Bash configuration.
    *   `postfix/`: Postfix mail server configurations.
        *   `main.cf`: Main Postfix configuration file.
        *   `postfix.sh`: Script to configure and start Postfix.
    *   `dnsmasq/`: Dnsmasq DNS forwarder configurations.
        *   `dnsmasq.conf`: Main Dnsmasq configuration file with security best practices and high-usage optimizations.
        *   `update_dnsmasq_upstream.sh`: Script to capture upstream DNS resolvers and configure the container to use dnsmasq on localhost.
    *   `scripts/`: Contains utility scripts.
        *   `trigger_temp_pipeline.sh`: Script to trigger a temporary GitLab CI/CD pipeline.
        *   `update-variables.sh`: Script to update GitLab CI/CD variables.

## Postfix Configuration

Postfix is configured to handle mail relaying. The `etc/postfix/postfix.sh` script dynamically updates the `main.cf` configuration based on environment variables, specifically for AWS ECS Fargate environments.

Key configurations handled by `postfix.sh`:

*   Sets `/etc/mailname` to `$CONTAINER_HOSTNAME`.
*   Replaces `CONTAINER_HOSTNAME` and `MAIL_HOST:MAIL_PORT` placeholders in `main.cf` with environment variable values.
*   Configures mail aliases for the `root` user to `$SYSADM_EMAIL`.

## Dnsmasq Configuration

Dnsmasq is configured as a secure DNS forwarder with security best practices and optimizations for high-usage scenarios. The configuration is designed for AWS ECS Fargate environments.

**Important:** The `update_dnsmasq_upstream.sh` script must be run in the dockerentry at the server image to:
* Capture upstream DNS resolvers from the container's `/etc/resolv.conf` (before it's changed)
* Generate `/etc/dnsmasq.upstream.conf` with the upstream nameservers (excluding loopback addresses)
* Configure the container to use dnsmasq on localhost (127.0.0.1) by updating `/etc/resolv.conf`

This ensures dnsmasq uses the correct upstream resolvers (typically the VPC resolver, e.g., 10.0.0.2) while the container itself uses dnsmasq for DNS resolution.

### Security Features

*   **DNSSEC Validation**: Enabled to prevent DNS spoofing and cache poisoning attacks.
*   **Rate Limiting**: Limits queries to 150 per second per source IP to prevent DNS amplification attacks.
*   **Interface Binding**: Binds to localhost (127.0.0.1) only, preventing external access in containerized environments.
*   **Bogus NXDOMAIN Protection**: Rejects DNS responses with private IP ranges to prevent DNS rebinding attacks.
*   **Query Size Limits**: Maximum query size restrictions to prevent buffer overflow attacks.
*   **DHCP Disabled**: Operates as DNS forwarder only (DHCP functionality disabled).
*   **Trusted Upstream Servers**: Uses only trusted DNS servers (Cloudflare 1.1.1.1, 1.0.0.1 and Google 8.8.8.8, 8.8.4.4).
*   **Query Logging**: Enabled for security monitoring and debugging.

### High Usage Optimizations

*   **Large Cache Size**: Configurable cache size (default 10,000 entries) for improved performance on repeated queries.
*   **Multiple Upstream Servers**: Four redundant DNS servers provide load balancing and failover.
*   **EDNS0 Support**: Enabled for better DNS response handling and larger packet sizes.
*   **Optimized Connection Handling**: Supports up to 150 concurrent DNS forward queries.
*   **TTL Optimization**: Configured local and negative cache TTL for optimal performance.

### Upstream Resolver Configuration

The `update_dnsmasq_upstream.sh` script automatically:
* Extracts upstream nameservers from `/etc/resolv.conf` (excluding loopback addresses like 127.0.0.1 and ::1)
* Writes them to `/etc/dnsmasq.upstream.conf` for dnsmasq to use
* Falls back to public resolvers (1.1.1.1 and 8.8.8.8) if no upstream resolvers are found

The script should be executed early in the container startup process (in dockerentry) before dnsmasq starts, to ensure the correct upstream resolvers are captured.

## Building the Docker Image

To build the Docker image, navigate to the root of this repository and run:

```bash
docker build -t your-image-name:tag .
```

## Usage

This image is intended as a base image. You can use it in your own Dockerfiles by referencing it in your `FROM` instruction:

```dockerfile
FROM your-image-name:tag
# Your application-specific layers
```

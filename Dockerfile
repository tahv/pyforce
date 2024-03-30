# Installation:
# https://www.perforce.com/manuals/p4sag/Content/P4SAG/install.linux.packages.install.html

# Post-installation configuration:
# https://www.perforce.com/manuals/p4sag/Content/P4SAG/install.linux.packages.configure.html

# Example perforce server:
# https://github.com/ambakshi/docker-perforce/tree/master/perforce-server

# Dockerfile from sourcegraph:
# https://github.com/sourcegraph/helix-docker/tree/main

# Making a Perforce Server with Docker compose
# https://aricodes.net/posts/perforce-server-with-docker/
ARG PYTHON_VERSION=3.11
FROM python:$PYTHON_VERSION

# Update Ubuntu and add Perforce Package Source
# Add the perforce public key to our keyring
# Add perforce repository to our APT config
RUN apt-get update && \
  apt-get install -y wget gnupg2 && \
  wget -qO - https://package.perforce.com/perforce.pubkey | apt-key add - && \
  echo "deb http://package.perforce.com/apt/ubuntu focal release" > /etc/apt/sources.list.d/perforce.list && \
  apt-get update

# Install helix-p4d, which installs p4d, p4, p4dctl, and a configuration script.
RUN apt-get update && apt-get install -y helix-p4d

WORKDIR /app

RUN python -m pip install pytest coverage

COPY . .

RUN python -m pip install --editable .

ENTRYPOINT ["/bin/sh", "-c"]

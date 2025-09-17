# Use Ubuntu 24.04 as base image
FROM ubuntu:24.04

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    ca-certificates \
    bash-completion \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN useradd -m -s /bin/bash vscode && \
    echo "vscode ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Install uv (Python package manager)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# Install just (command runner)
RUN curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh | bash -s -- --to /usr/local/bin

# Set up just tab completion for bash
RUN mkdir -p /etc/bash_completion.d && \
    just --completions bash > /etc/bash_completion.d/just

# Switch to vscode user and set up their environment
USER vscode
WORKDIR /home/vscode

# Install uv for the vscode user
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/home/vscode/.cargo/bin:$PATH"

# Add just completion to user's bashrc
RUN echo "source /etc/bash_completion.d/just" >> /home/vscode/.bashrc

# Set the working directory to the workspace
WORKDIR /workspaces/otelmewhy

# Default command
CMD ["/bin/bash"]

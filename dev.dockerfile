FROM ubuntu:22.04

WORKDIR /root/
COPY . /root/

RUN apt-get update -y && \
    apt-get install -y --no-install-recommends \
      libelf1 libelf-dev zlib1g-dev libclang-dev \
      make git clang llvm pkg-config build-essential curl ca-certificates && \
    update-ca-certificates && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Match the CI major version; NodeSource tracks the newest Node 24 release.
RUN curl -fsSL https://deb.nodesource.com/setup_24.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

ENV RUSTUP_HOME=/opt/rustup \
    CARGO_HOME=/opt/cargo \
    PATH=/opt/cargo/bin:$PATH
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | \
    sh -s -- -y --profile minimal --default-toolchain stable \
      --component clippy --target wasm32-wasip2 --no-modify-path

ENTRYPOINT ["/bin/bash"]

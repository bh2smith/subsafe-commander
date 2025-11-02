# Multi-stage Dockerfile for SubSafe Commander (Rust)

# Build stage
FROM rustlang/rust:nightly AS builder

WORKDIR /app

# Copy Cargo files
COPY Cargo.toml ./

# Copy source code
COPY src ./src

# Build the application in release mode
RUN cargo build --release

# Runtime stage
FROM debian:bookworm-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Copy the binary from builder
COPY --from=builder /app/target/release/subsafe-commander /usr/local/bin/

# Set the entrypoint
ENTRYPOINT ["subsafe-commander"]

# Default command (can be overridden)
CMD ["--help"]


#!/bin/bash
# =============================================================================
# RPM Build Script for AgentSight
# =============================================================================
# This script builds the agentsight binary and creates a source tarball
# for RPM package building.
#
# Usage:
#   ./scripts/rpm-build.sh [options]
#
# Options:
#   -v, --version VERSION    Specify version (default: from Cargo.toml)
#   -o, --output DIR         Output directory (default: ./rpm-sources)
#   -h, --help               Show this help message
#
# The script will:
#   1. Build frontend (npm install && npm run build:embed)
#   2. Build Rust binary (cargo build --release)
#   3. Create a tarball: agentsight-<version>.tar.gz
#   4. The tarball contains: agentsight, agentsight.service, README.md, README_CN.md, LICENSE
# =============================================================================

set -e

# =============================================================================
# Configuration
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
OUTPUT_DIR="${PROJECT_ROOT}/rpm-sources"

# Default version from Cargo.toml
VERSION=$(grep -m1 '^version' "$PROJECT_ROOT/Cargo.toml" | sed 's/version = "\(.*\)"/\1/')

# =============================================================================
# Helper Functions
# =============================================================================

show_help() {
    cat << EOF
RPM Build Script for AgentSight

Usage: $(basename "$0") [options]

Options:
    -v, --version VERSION    Specify version (default: $VERSION)
    -o, --output DIR         Output directory (default: ./rpm-sources)
    -h, --help               Show this help message

The script will:
    1. Build frontend (npm install && npm run build:embed)
    2. Build Rust binary (cargo build --release)
    3. Create a tarball: agentsight-<version>.tar.gz
    4. The tarball contains: agentsight, agentsight.service, README.md, README_CN.md, LICENSE

Example:
    $(basename "$0")                    # Build with default version
    $(basename "$0") -v 0.2.0           # Build with specific version
    $(basename "$0") -o /tmp/rpm        # Output to specific directory
EOF
}

log_info() {
    echo -e "\033[32m[INFO]\033[0m $1"
}

log_error() {
    echo -e "\033[31m[ERROR]\033[0m $1" >&2
}

# =============================================================================
# Parse Arguments
# =============================================================================

while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--version)
            VERSION="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# =============================================================================
# Build Process
# =============================================================================

log_info "Building AgentSight RPM source tarball"
log_info "Version: $VERSION"
log_info "Project root: $PROJECT_ROOT"
log_info "Output directory: $OUTPUT_DIR"

# Change to project root
cd "$PROJECT_ROOT"

# Step 1: Build the binary (with frontend embedded)
log_info "Building agentsight binary (release mode)..."

# Build frontend first
log_info "Building frontend..."
cd "$PROJECT_ROOT/dashboard"
if [[ ! -d "node_modules" ]]; then
    npm install
fi
npm run build:embed

# Build Rust binary
log_info "Building Rust binary..."
cd "$PROJECT_ROOT"
cargo build --release

# Verify binary exists
if [[ ! -f "target/release/agentsight" ]]; then
    log_error "Binary not found: target/release/agentsight"
    exit 1
fi

log_info "Binary built successfully"

# Step 2: Prepare tarball contents
TARBALL_NAME="agentsight-${VERSION}"
TARBALL_DIR="${OUTPUT_DIR}/${TARBALL_NAME}"

log_info "Preparing tarball contents..."
mkdir -p "$TARBALL_DIR"

# Copy required files
cp "target/release/agentsight" "$TARBALL_DIR/"
cp "$PROJECT_ROOT/scripts/agentsight.service" "$TARBALL_DIR/"
cp "$PROJECT_ROOT/README.md" "$TARBALL_DIR/"
cp "$PROJECT_ROOT/README_CN.md" "$TARBALL_DIR/"
cp "$PROJECT_ROOT/LICENSE" "$TARBALL_DIR/"

log_info "Files prepared in: $TARBALL_DIR"

# Step 3: Create tarball
log_info "Creating tarball..."
mkdir -p "$OUTPUT_DIR"
cd "$OUTPUT_DIR"

tar -czvf "${TARBALL_NAME}.tar.gz" "$TARBALL_NAME"

TARBALL_PATH="${OUTPUT_DIR}/${TARBALL_NAME}.tar.gz"
log_info "Tarball created: $TARBALL_PATH"

# Step 4: Show summary
echo ""
echo "=========================================="
log_info "Build completed successfully!"
echo "=========================================="
echo "Tarball: $TARBALL_PATH"
echo ""
echo "To build RPM package:"
echo "  1. Copy spec file: cp agentsight.spec ~/rpmbuild/SPECS/"
echo "  2. Copy tarball:   cp ${TARBALL_NAME}.tar.gz ~/rpmbuild/SOURCES/"
echo "  3. Build RPM:      rpmbuild -bb ~/rpmbuild/SPECS/agentsight.spec"
echo ""

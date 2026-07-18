SYNC_VENDOR ?= 0

build: SYNC_VENDOR=1
build: build-frontend build-vis build-bpf build-rust

build-frontend:
	cd frontend && npm install && npm run build

build-vis:
	cd vis && npm ci && npm run build
	cp vis/dist/repository-nebula.iife.js collector/vendor/vis/

build-bpf:
	make -C bpf

build-rust:
	cd collector && AGENTSIGHT_SYNC_VENDOR=$(SYNC_VENDOR) cargo build --release

clean:
	make -C bpf clean
	cd collector && cargo clean
	cd frontend && rm -rf .next node_modules dist
	cd vis && rm -rf node_modules dist

install:
	sudo apt update
	sudo apt-get install -y --no-install-recommends \
        libelf1 libelf-dev zlib1g-dev \
        make clang llvm
	# Install Node.js if not present
	@command -v node >/dev/null 2>&1 || { \
		echo "Installing Node.js..."; \
		curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -; \
		sudo apt-get install -y nodejs; \
	}
	# Install Rust if not present
	@command -v cargo >/dev/null 2>&1 || { \
		echo "Installing Rust..."; \
		curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y; \
		source ~/.cargo/env; \
	}

test: test-vis
	make -C bpf test
	cd collector && cargo test
	cd frontend && npm run build

test-vis:
	cd vis && npm ci && npm run build
	cmp vis/dist/repository-nebula.iife.js collector/vendor/vis/repository-nebula.iife.js

.PHONY: build build-frontend build-vis build-bpf build-rust clean install test test-vis

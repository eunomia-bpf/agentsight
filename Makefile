SYNC_VENDOR ?= 0

build: SYNC_VENDOR=1
build: build-frontend build-vis build-bpf build-rust

build-frontend:
	cd frontend && npm install && npm run build

build-vis:
	cd ext/vis/web && npm ci && npm run build
	cp ext/vis/web/dist/repository-nebula.iife.js ext/vis/vendor/vis/

build-bpf:
	make -C bpf

build-rust:
	cd ext/vis && cargo build --release
	cd collector && AGENTSIGHT_SYNC_VENDOR=$(SYNC_VENDOR) cargo build --release

clean:
	make -C bpf clean
	cd agentsight-capture && cargo clean
	cd agentsight-protocol && cargo clean
	cd ext/analysis && cargo clean
	cd ext/runtime && cargo clean
	cd ext/session && cargo clean
	cd ext/vis && cargo clean
	cd ext/pprof && cargo clean
	cd collector && cargo clean
	cd frontend && rm -rf .next node_modules dist
	cd ext/vis/web && rm -rf node_modules dist

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
	cd agentsight-capture && cargo test
	cd agentsight-protocol && cargo test
	cd compat/agentsight-capture && cargo test
	cd ext/analysis && cargo test
	cd ext/runtime && cargo test
	cd ext/session && cargo test
	cd ext/vis && cargo test
	cd ext/pprof && cargo test
	cd collector && cargo test
	cd frontend && npm run test:workers && npm run build

test-vis:
	cd ext/vis/web && npm ci && npm test && npm run build
	cmp ext/vis/web/dist/repository-nebula.iife.js ext/vis/vendor/vis/repository-nebula.iife.js

.PHONY: build build-frontend build-vis build-bpf build-rust clean install test test-vis

# =============================================================================
# BUILD
# =============================================================================

.PHONY: build
build: ## Build agentsight binary
	cargo build --release

# =============================================================================
# INSTALL
# =============================================================================

PREFIX ?= /usr/local

.PHONY: install
install: ## Install agentsight binary and set BPF capabilities
	install -d -m 0755 $(DESTDIR)$(PREFIX)/bin
	install -p -m 0755 target/release/agentsight $(DESTDIR)$(PREFIX)/bin/
	setcap cap_bpf,cap_perfmon=ep $(DESTDIR)$(PREFIX)/bin/agentsight

.PHONY: help
help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help

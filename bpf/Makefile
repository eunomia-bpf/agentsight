# SPDX-License-Identifier: (LGPL-2.1 OR BSD-2-Clause)
OUTPUT := .output
CLANG ?= clang
LIBBPF_SRC := $(abspath ../libbpf/src)
BPFTOOL_SRC := $(abspath ../bpftool/src)
LIBBPF_OBJ := $(abspath $(OUTPUT)/libbpf.a)
BPFTOOL_OUTPUT ?= $(abspath $(OUTPUT)/bpftool)
BPFTOOL ?= $(BPFTOOL_OUTPUT)/bootstrap/bpftool
LIBBLAZESYM_SRC := $(abspath ..//blazesym/)
LIBBLAZESYM_OBJ := $(abspath $(OUTPUT)/libblazesym.a)
LIBBLAZESYM_HEADER := $(abspath $(OUTPUT)/blazesym.h)
ARCH ?= $(shell uname -m | sed 's/x86_64/x86/' \
			 | sed 's/arm.*/arm/' \
			 | sed 's/aarch64/arm64/' \
			 | sed 's/ppc64le/powerpc/' \
			 | sed 's/mips.*/mips/' \
			 | sed 's/riscv64/riscv/' \
			 | sed 's/loongarch64/loongarch/')
VMLINUX := ../vmlinux/$(ARCH)/vmlinux.h
# Use our own libbpf API headers and Linux UAPI headers distributed with
# libbpf to avoid dependency on system-wide headers, which could be missing or
# outdated
INCLUDES := -I$(OUTPUT) -I. -I../libbpf/include/uapi -I$(dir $(VMLINUX))
CFLAGS := -g -Wall
ALL_LDFLAGS := $(LDFLAGS) $(EXTRA_LDFLAGS)

# AddressSanitizer flags
ifdef ASAN
ASAN_FLAGS := -fsanitize=address -fno-omit-frame-pointer -O1 -g
CFLAGS += $(ASAN_FLAGS)
ALL_LDFLAGS += $(ASAN_FLAGS)
endif

APPS = sslsniff process process_new test_process_utils test_process_filter test_process_new_map_flush test_process_new_mem_info test_process_new_header # minimal minimal_legacy uprobe kprobe fentry usdt sockfilter tc ksyscall

# All test programs (no BPF skeleton needed)
TEST_APPS = test_process_utils test_process_filter test_process_new_map_flush test_process_new_mem_info test_process_new_header

CARGO ?= $(shell which cargo)
ifeq ($(strip $(CARGO)),)
BZS_APPS :=
else
BZS_APPS := # profile
APPS += $(BZS_APPS)
# Required by libblazesym
ALL_LDFLAGS += -lrt -ldl -lpthread -lm
endif

# Get Clang's default includes on this system. We'll explicitly add these dirs
# to the includes list when compiling with `-target bpf` because otherwise some
# architecture-specific dirs will be "missing" on some architectures/distros -
# headers such as asm/types.h, asm/byteorder.h, asm/socket.h, asm/sockios.h,
# sys/cdefs.h etc. might be missing.
#
# Use '-idirafter': Don't interfere with include mechanics except where the
# build would have failed anyways.
CLANG_BPF_SYS_INCLUDES ?= $(shell $(CLANG) -v -E - </dev/null 2>&1 \
	| sed -n '/<...> search starts here:/,/End of search list./{ s| \(/.*\)|-idirafter \1|p }')

ifeq ($(V),1)
	Q =
	msg =
else
	Q = @
	msg = @printf '  %-8s %s%s\n'					\
		      "$(1)"						\
		      "$(patsubst $(abspath $(OUTPUT))/%,%,$(2))"	\
		      "$(if $(3), $(3))";
	MAKEFLAGS += --no-print-directory
endif

define allow-override
  $(if $(or $(findstring environment,$(origin $(1))),\
            $(findstring command line,$(origin $(1)))),,\
    $(eval $(1) = $(2)))
endef

$(call allow-override,CC,$(CROSS_COMPILE)cc)
$(call allow-override,LD,$(CROSS_COMPILE)ld)

.PHONY: all
all: $(APPS)

.PHONY: debug
debug:
	$(MAKE) ASAN=1 all

.PHONY: sslsniff-debug
sslsniff-debug:
	$(MAKE) ASAN=1 sslsniff

.PHONY: clean
clean:
	$(call msg,CLEAN)
	$(Q)rm -rf $(OUTPUT) $(APPS)

.PHONY: help
help:
	@echo "Available targets:"
	@echo "  all          - Build all applications"
	@echo "  sslsniff     - Build sslsniff only"
	@echo "  process      - Build process tracer only"
	@echo "  test         - Build and run tests"
	@echo "  debug        - Build all applications with AddressSanitizer"
	@echo "  sslsniff-debug - Build sslsniff with AddressSanitizer"
	@echo "  clean        - Clean build artifacts"
	@echo ""
	@echo "Build with AddressSanitizer manually:"
	@echo "  make ASAN=1 sslsniff"

.PHONY: test
test: test_process_utils test_process_filter test_process_new_map_flush test_process_new_mem_info test_process_new_header
	@echo "Running process_utils tests..."
	@./test_process_utils
	@echo ""
	@echo "Running process_filter tests..."
	@./test_process_filter
	@echo ""
	@echo "Running process_new map_flush tests..."
	@./test_process_new_map_flush
	@echo ""
	@echo "Running process_new mem_info tests..."
	@./test_process_new_mem_info
	@echo ""
	@echo "Running process_new header tests..."
	@./test_process_new_header

.PHONY: integration-test
integration-test: process_new process
	@echo "Running integration tests (requires sudo)..."
	@sudo python3 tests/test_integration.py

$(OUTPUT) $(OUTPUT)/libbpf $(BPFTOOL_OUTPUT):
	$(call msg,MKDIR,$@)
	$(Q)mkdir -p $@

# Build libbpf
$(LIBBPF_OBJ): $(wildcard $(LIBBPF_SRC)/*.[ch] $(LIBBPF_SRC)/Makefile) | $(OUTPUT)/libbpf
	$(call msg,LIB,$@)
	$(Q)$(MAKE) -C $(LIBBPF_SRC) BUILD_STATIC_ONLY=1		      \
		    OBJDIR=$(dir $@)/libbpf DESTDIR=$(dir $@)		      \
		    INCLUDEDIR= LIBDIR= UAPIDIR=			      \
		    install

# Build bpftool
$(BPFTOOL): | $(BPFTOOL_OUTPUT)
	$(call msg,BPFTOOL,$@)
	$(Q)$(MAKE) ARCH= CROSS_COMPILE= OUTPUT=$(BPFTOOL_OUTPUT)/ -C $(BPFTOOL_SRC) bootstrap


$(LIBBLAZESYM_SRC)/target/release/libblazesym.a::
	$(Q)cd $(LIBBLAZESYM_SRC) && $(CARGO) build --features=cheader,dont-generate-test-files --release

$(LIBBLAZESYM_OBJ): $(LIBBLAZESYM_SRC)/target/release/libblazesym.a | $(OUTPUT)
	$(call msg,LIB, $@)
	$(Q)cp $(LIBBLAZESYM_SRC)/target/release/libblazesym.a $@

$(LIBBLAZESYM_HEADER): $(LIBBLAZESYM_SRC)/target/release/libblazesym.a | $(OUTPUT)
	$(call msg,LIB,$@)
	$(Q)cp $(LIBBLAZESYM_SRC)/target/release/blazesym.h $@

# Extra dependencies for process_new BPF (subdirectory headers)
$(OUTPUT)/process_new.bpf.o: $(wildcard process_ext/*.h)

# Build BPF code
$(OUTPUT)/%.bpf.o: %.bpf.c $(LIBBPF_OBJ) $(wildcard %.h) $(VMLINUX) | $(OUTPUT) $(BPFTOOL)
	$(call msg,BPF,$@)
	$(Q)$(CLANG) -g -O2 -target bpf -D__TARGET_ARCH_$(ARCH)		      \
		     $(INCLUDES) $(CLANG_BPF_SYS_INCLUDES)		      \
		     -c $(filter %.c,$^) -o $(patsubst %.bpf.o,%.tmp.bpf.o,$@)
	$(Q)$(BPFTOOL) gen object $@ $(patsubst %.bpf.o,%.tmp.bpf.o,$@)

# Generate BPF skeletons
$(OUTPUT)/%.skel.h: $(OUTPUT)/%.bpf.o | $(OUTPUT) $(BPFTOOL)
	$(call msg,GEN-SKEL,$@)
	$(Q)$(BPFTOOL) gen skeleton $< > $@

# Build user-space code (exclude all test programs from the skel.h requirement)
$(patsubst %,$(OUTPUT)/%.o,$(filter-out $(TEST_APPS),$(APPS))): %.o: %.skel.h

# Special rule for test programs (no BPF skeleton needed)
$(OUTPUT)/test_process_utils.o: test_process_utils.c $(wildcard *.h) | $(OUTPUT)
	$(call msg,CC,$@)
	$(Q)$(CC) $(CFLAGS) $(INCLUDES) -c $< -o $@

$(OUTPUT)/test_process_filter.o: test_process_filter.c $(wildcard *.h) | $(OUTPUT)
	$(call msg,CC,$@)
	$(Q)$(CC) $(CFLAGS) $(INCLUDES) -c $< -o $@

$(OUTPUT)/test_process_new_map_flush.o: tests/test_process_new_map_flush.c $(wildcard *.h) $(wildcard process_ext/*.h) | $(OUTPUT)
	$(call msg,CC,$@)
	$(Q)$(CC) $(CFLAGS) -I. -Itests -c $< -o $@

$(OUTPUT)/test_process_new_mem_info.o: tests/test_process_new_mem_info.c $(wildcard *.h) $(wildcard process_ext/*.h) | $(OUTPUT)
	$(call msg,CC,$@)
	$(Q)$(CC) $(CFLAGS) -I. -c $< -o $@

$(OUTPUT)/test_process_new_header.o: tests/test_process_new_header.c $(wildcard *.h) $(wildcard process_ext/*.h) | $(OUTPUT)
	$(call msg,CC,$@)
	$(Q)$(CC) $(CFLAGS) -I. -c $< -o $@

$(OUTPUT)/%.o: %.c $(wildcard %.h) | $(OUTPUT)
	$(call msg,CC,$@)
	$(Q)$(CC) $(CFLAGS) $(INCLUDES) -c $(filter %.c,$^) -o $@

$(patsubst %,$(OUTPUT)/%.o,$(BZS_APPS)): $(LIBBLAZESYM_HEADER)

$(BZS_APPS): $(LIBBLAZESYM_OBJ)

# Build application binary (exclude all test programs)
$(filter-out $(TEST_APPS),$(APPS)): %: $(OUTPUT)/%.o $(LIBBPF_OBJ) | $(OUTPUT)
	$(call msg,BINARY,$@)
	$(Q)$(CC) $(CFLAGS) $^ $(ALL_LDFLAGS) -lelf -lz -o $@

# Special rules for test programs (no libbpf needed)
test_process_utils: $(OUTPUT)/test_process_utils.o | $(OUTPUT)
	$(call msg,BINARY,$@)
	$(Q)$(CC) $(CFLAGS) $^ $(ALL_LDFLAGS) -o $@

test_process_filter: $(OUTPUT)/test_process_filter.o | $(OUTPUT)
	$(call msg,BINARY,$@)
	$(Q)$(CC) $(CFLAGS) $^ $(ALL_LDFLAGS) -o $@

# map_flush helper uses libbpf_num_possible_cpus() from libbpf.
test_process_new_map_flush: $(OUTPUT)/test_process_new_map_flush.o $(LIBBPF_OBJ) | $(OUTPUT)
	$(call msg,BINARY,$@)
	$(Q)$(CC) $(CFLAGS) $^ $(ALL_LDFLAGS) -lelf -lz -o $@

test_process_new_mem_info: $(OUTPUT)/test_process_new_mem_info.o | $(OUTPUT)
	$(call msg,BINARY,$@)
	$(Q)$(CC) $(CFLAGS) $^ $(ALL_LDFLAGS) -o $@

test_process_new_header: $(OUTPUT)/test_process_new_header.o | $(OUTPUT)
	$(call msg,BINARY,$@)
	$(Q)$(CC) $(CFLAGS) $^ $(ALL_LDFLAGS) -o $@

# delete failed targets
.DELETE_ON_ERROR:

# keep intermediate (.skel.h, .bpf.o, etc) targets
.SECONDARY:

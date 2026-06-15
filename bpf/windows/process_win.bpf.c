// SPDX-License-Identifier: (LGPL-2.1 OR BSD-2-Clause)
//
// process_win.bpf.c -- AgentSight process lifecycle on eBPF-for-Windows.
//
// Linux analog: bpf/process.bpf.c handle_exec()/handle_exit() which attach to
// the sched_process_exec / sched_process_exit tracepoints. eBPF-for-Windows has
// no tracepoints, but the `ntosebpfext` extension provides
// EBPF_PROGRAM_TYPE_PROCESS, which invokes the program on process CREATE and
// DELETE via PsSetCreateProcessNotifyRoutineEx. The typed context process_md_t
// carries pid/parent, command line, and exit code -- enough to reproduce the
// EXEC/EXIT JSONL the collector already consumes.
//
// Build (on a Windows dev box with the LLVM + eBPF-for-Windows toolchain):
//   clang -target bpf -O2 -g -Ibpf/windows -c bpf/windows/process_win.bpf.c \
//         -o build/process_win.o
// Verify (this is our program's "conformance" gate):
//   netsh ebpf show verification build/process_win.o process
//
// Requires the eBPF-for-Windows headers (NuGet `eBPF-for-Windows`) and the
// ntosebpfext process header on the include path.
#include "bpf_helpers.h"
#include "ntos_ebpf_ext_process_hook.h" // defines process_md_t, PROCESS_OPERATION_*
#include "bpf_windows.h"

// Ring buffer carrying as_process_record to userspace. Linux-compatible API.
struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 256 * 1024);
} process_rb SEC(".maps");

// Per-CPU scratch to build a record before bpf_ringbuf_output(), because
// eBPF-for-Windows does not yet expose ringbuf reserve/submit (issue #727).
struct {
    __uint(type, BPF_MAP_TYPE_PERCPU_ARRAY);
    __uint(max_entries, 1);
    __type(key, __u32);
    __type(value, struct as_process_record);
} scratch SEC(".maps");

// Optional PID filter, set from userspace (0 = trace all). Mirrors targ_pid.
const volatile unsigned int targ_pid = 0;

static __inline struct as_process_record *get_scratch(void)
{
    __u32 zero = 0;
    return bpf_map_lookup_elem(&scratch, &zero);
}

SEC("process")
int as_process_monitor(process_md_t *ctx)
{
    unsigned int pid = (unsigned int)ctx->process_id;
    if (targ_pid && targ_pid != pid)
        return 0;

    struct as_process_record *r = get_scratch();
    if (!r)
        return 0;

    r->pid = pid;
    r->ppid = (unsigned int)ctx->parent_process_id;
    r->timestamp_ns = bpf_ktime_get_boot_ns();
    r->logon_id = bpf_get_current_logon_id();
    r->exit_code = 0;
    r->cmd_len = 0;
    r->cmdline[0] = '\0';

    if (ctx->operation == PROCESS_OPERATION_CREATE) {
        r->kind = AS_REC_PROCESS_EXEC;

        // command_start..command_end is the verified command-line buffer in ctx.
        // Bound the length to a compile-time constant so PREVAIL can prove the
        // copy is safe (same discipline as the Linux verifier path).
        unsigned int len = 0;
        if (ctx->command_end > ctx->command_start)
            len = (unsigned int)(ctx->command_end - ctx->command_start);
        if (len > AS_CMDLINE_LEN - 1)
            len = AS_CMDLINE_LEN - 1;
        if (len > 0)
            bpf_memcpy_s(r->cmdline, AS_CMDLINE_LEN - 1, ctx->command_start, len);
        r->cmdline[len] = '\0';
        r->cmd_len = len;
    } else { // PROCESS_OPERATION_DELETE
        r->kind = AS_REC_PROCESS_EXIT;
        r->exit_code = ctx->exit_code;
    }

    bpf_ringbuf_output(&process_rb, r, sizeof(*r), 0);
    return 0;
}

char LICENSE[] SEC("license") = "Dual BSD/GPL";

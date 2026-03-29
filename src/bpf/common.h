#ifndef COMMON_H
#define COMMON_H

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>

#ifndef RING_BUFFER_SIZE
#define RING_BUFFER_SIZE (64 * 1024 * 1024)
#endif

#ifndef MAX_TRACED_PROCESSES
#define MAX_TRACED_PROCESSES 1024
#endif


// Event source identifiers - first field of every ringbuffer event
// Allows unified dispatch from a shared ring buffer
typedef enum {
    EVENT_SOURCE_PROC = 1,   // Process events (proctrace)
    EVENT_SOURCE_SSL  = 2,   // SSL/TLS traffic events (sslsniff)
    EVENT_SOURCE_PROCMON = 3, // Process monitor events (procmon)
} event_source_t;

// Common event header - every ringbuffer event MUST start with this
// Allows user-space to read source and dispatch to the right handler
struct common_event_hdr {
    u32 source;  // event_source_t - identifies the event producer
};

// Shared ring buffer - used by all BPF programs to avoid wasting memory
struct
{
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, RING_BUFFER_SIZE);
} rb SEC(".maps");

#ifndef NO_TRACED_PROCESSES_MAP
// Shared traced_processes map - used by all BPF programs for process filtering
struct
{
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, MAX_TRACED_PROCESSES);
    __type(key, u32);
    __type(value, u32);
} traced_processes SEC(".maps");
#endif

#endif

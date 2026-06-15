# Conformance & verification harness

Two distinct things get confused under the word "conformance"; this harness covers
both, because the project goal touches each:

## Layer 0 — Local reference execution (uBPF, runs on Linux) ✅ EXECUTED

`run_local_ubpf.py` assembles the `vectors/*.data` ISA tests and executes them on
the **uBPF** reference runtime — the same userspace interpreter eBPF-for-Windows
uses for its *interpreted* execution mode. This is the conformance layer that can
actually run in a Linux dev environment / CI, and it has been executed:

```
$ python3 run_local_ubpf.py --plugin /path/to/ubpf_plugin
PASS add_alu64.data       expected=0xc  got='c'
PASS alu_reg.data         expected=0x1e got='1e'
PASS and_imm.data         expected=0xf  got='f'
PASS jgt_taken.data       expected=0x5  got='5'
PASS jne_fallthrough.data expected=0x9  got='9'
PASS jump_taken.data      expected=0x1  got='1'
PASS lsh_imm.data         expected=0x10 got='10'
PASS mov64_exit.data      expected=0x2a got='2a'
8/8 vectors passed on the uBPF reference runtime.
```

Coverage: immediate ALU (mov/add/and/lsh), register-to-register ALU, and three
jump conditions (jeq/jne/jgt, taken and fall-through). This proves our vectors are
valid eBPF ISA and that a conformant runtime executes them correctly. It does **not**
prove eBPF-for-Windows itself passes — that is Layers 1–2, which need a Windows host.

Build the plugin (no Boost needed):
```
git clone --recurse-submodules https://github.com/iovisor/ubpf
cd ubpf && cmake -B build -S . -DUBPF_ENABLE_TESTS=ON -DCMAKE_BUILD_TYPE=Release
cmake --build build --target ubpf          # libubpf.a
g++ -std=c++20 -O2 -o ubpf_plugin ubpf_plugin/ubpf_plugin.cc \
    -Ivm -Ivm/inc -Ibuild/vm -Iubpf_plugin build/lib/libubpf.a
```

## Layer 1 — Runtime ISA conformance (`bpf_conformance`)

[`Alan-Jowett/bpf_conformance`](https://github.com/Alan-Jowett/bpf_conformance)
measures how faithfully a **runtime** implements the eBPF **instruction set**. It
feeds bytecode + initial memory to a runtime plugin and checks the resulting `r0`.
It tests instruction semantics only — *not* program types, hooks, maps, or helpers.

eBPF-for-Windows ships conformance plugins for its three execution modes (`bpf2c`,
JIT, interpreter) and is run against these vectors. "Passing the conformance suite on
Windows" is this layer, and it is a property of the **runtime**, not of AgentSight.
`run_conformance.ps1` clones the suite, builds the runner, and executes both the
suite's authoritative vectors and the smoke vectors in `vectors/` against the plugin.

`vectors/*.data` here are tiny smoke tests in the suite's `.data` format
(`-- asm` / `-- mem` / `-- result`) — enough to prove the harness wiring end to end.
The authoritative coverage is the suite's own `tests/` directory.

## Layer 2 — AgentSight program verification (PREVAIL)

The meaningful conformance gate for **our** programs is that they are written in the
verifiable/conformant subset and pass the PREVAIL verifier:

```
netsh ebpf show verification build\process_win.o  process
netsh ebpf show verification build\sockaddr_win.o cgroup/connect4
netsh ebpf show verification build\sockops_win.o  sockops
```

`run_conformance.ps1` runs all of these and returns non-zero if any program fails to
verify, so CI (windows-latest) can gate the migration on it.

## Why this isn't run in the Linux dev environment

Both layers require a Windows host with eBPF-for-Windows installed (and test-signing
mode for native-driver loading). This folder is the executable specification of the
gate; the GitHub Actions `windows` job (see `.github/workflows/`) is where it runs.

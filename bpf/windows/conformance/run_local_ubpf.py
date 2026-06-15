#!/usr/bin/env python3
"""Local conformance check: run our ISA `.data` vectors on the uBPF reference
runtime and verify r0 matches the expected result.

This is the Linux-runnable layer of conformance. eBPF-for-Windows itself can only
be exercised on a Windows host (run_conformance.ps1), but uBPF is the same
userspace interpreter eBPF-for-Windows uses for its *interpreted* execution mode,
so passing here proves our vectors are valid eBPF ISA and that a conformant
runtime executes them correctly.

Usage:
    python3 run_local_ubpf.py --plugin /path/to/ubpf_plugin [--dir vectors]

Build the plugin from iovisor/ubpf:
    cmake -B build -S . -DUBPF_ENABLE_TESTS=ON -DCMAKE_BUILD_TYPE=Release
    cmake --build build --target ubpf      # builds libubpf.a
    g++ -std=c++20 -O2 -o ubpf_plugin ubpf_plugin/ubpf_plugin.cc \\
        -Ivm -Ivm/inc -Ibuild/vm -Iubpf_plugin build/lib/libubpf.a
"""
import argparse, glob, os, re, subprocess, sys

# Minimal eBPF assembler covering the instructions our vectors use.
# Encoding: [opcode:1][src<<4|dst:1][offset:2 LE][imm:4 LE].
OPC = {
    "mov64": (0xb7, 0xbf), "mov32": (0xb4, 0xbc),
    "add64": (0x07, 0x0f), "add32": (0x04, 0x0c),
    "and64": (0x57, 0x5f), "or64": (0x47, 0x4f), "lsh64": (0x67, 0x6f),
    "jeq": (0x15, 0x1d), "jne": (0x55, 0x5d), "jgt": (0x25, 0x2d),
}
JMP = {"jeq", "jne", "jgt"}

def reg(tok):
    m = re.fullmatch(r"%?r(\d+)", tok.strip())
    if not m: raise ValueError(f"bad register: {tok}")
    return int(m.group(1))

def imm_bytes(v):
    return (v & 0xffffffff).to_bytes(4, "little")

def assemble(asm):
    out = bytearray()
    for raw in asm.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line: continue
        parts = re.split(r"[ \t]+", line, maxsplit=1)
        op = parts[0]
        args = [a.strip() for a in parts[1].split(",")] if len(parts) > 1 else []
        if op == "exit":
            out += bytes([0x95, 0, 0, 0, 0, 0, 0, 0]); continue
        if op == "ja":
            off = int(args[0], 0)
            out += bytes([0x05, 0]) + (off & 0xffff).to_bytes(2, "little") + imm_bytes(0)
            continue
        if op not in OPC: raise ValueError(f"unsupported op: {op}")
        k_op, x_op = OPC[op]
        if op in JMP:
            dst = reg(args[0]); off = int(args[2], 0)
            if re.fullmatch(r"%?r\d+", args[1].strip()):
                src = reg(args[1])
                out += bytes([x_op, (src << 4) | dst]) + (off & 0xffff).to_bytes(2, "little") + imm_bytes(0)
            else:
                out += bytes([k_op, dst]) + (off & 0xffff).to_bytes(2, "little") + imm_bytes(int(args[1], 0))
        else:
            dst = reg(args[0])
            if re.fullmatch(r"%?r\d+", args[1].strip()):
                src = reg(args[1])
                out += bytes([x_op, (src << 4) | dst, 0, 0]) + imm_bytes(0)
            else:
                out += bytes([k_op, dst, 0, 0]) + imm_bytes(int(args[1], 0))
    return bytes(out)

def parse_data(text):
    asm, result = None, None
    cur, buf = None, []
    for line in text.splitlines():
        m = re.match(r"^--\s*(\w+)", line)
        if m:
            if cur == "asm": asm = "\n".join(buf)
            elif cur == "result": result = "\n".join(buf).strip()
            cur, buf = m.group(1), []
        elif cur:
            buf.append(line)
    if cur == "asm": asm = "\n".join(buf)
    elif cur == "result": result = "\n".join(buf).strip()
    return asm, result

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plugin", required=True)
    ap.add_argument("--dir", default=os.path.join(os.path.dirname(__file__), "vectors"))
    args = ap.parse_args()

    files = sorted(glob.glob(os.path.join(args.dir, "*.data")))
    if not files:
        print(f"no .data vectors in {args.dir}", file=sys.stderr); return 1
    fails = 0
    for f in files:
        asm, expected = parse_data(open(f).read())
        if asm is None or expected is None:
            print(f"SKIP {os.path.basename(f)} (no asm/result)"); continue
        code = assemble(asm)
        hexs = " ".join(f"{b:02x}" for b in code)
        r = subprocess.run([args.plugin], input=hexs, capture_output=True, text=True)
        got = r.stdout.strip()
        exp = expected.lower().replace("0x", "")
        got_n = int(got, 16) if got else None
        exp_n = int(exp, 16) if exp else None
        ok = got_n == exp_n
        print(f"{'PASS' if ok else 'FAIL'} {os.path.basename(f):20} expected=0x{exp_n:x} got={got!r}")
        if not ok: fails += 1
    print(f"\n{len(files) - fails}/{len(files)} vectors passed on the uBPF reference runtime.")
    return 1 if fails else 0

if __name__ == "__main__":
    sys.exit(main())

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

export function shouldConfigureDirect(hasLocalDirect, hasAccountDirect, relayOnline) {
  return !hasLocalDirect && !hasAccountDirect && !relayOnline;
}

export async function tryNodeTransports(attempts) {
  const failures = [];
  for (const { transport, open } of attempts) {
    try {
      await open();
      return { transport, failures };
    } catch (cause) {
      failures.push({ transport, cause });
    }
  }
  return { transport: null, failures };
}

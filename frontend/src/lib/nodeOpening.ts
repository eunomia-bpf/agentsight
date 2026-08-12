// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

export function shouldConfigureDirect(
  hasLocalDirect: boolean,
  hasAccountDirect: boolean,
  relayOnline: boolean,
): boolean {
  return !hasLocalDirect && !hasAccountDirect && !relayOnline;
}

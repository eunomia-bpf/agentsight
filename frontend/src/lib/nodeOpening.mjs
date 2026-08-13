// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

export function shouldConfigureDirect(hasLocalDirect, hasAccountDirect, relayOnline) {
  return !hasLocalDirect && !hasAccountDirect && !relayOnline;
}

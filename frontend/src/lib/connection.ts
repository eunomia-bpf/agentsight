// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

// Compatibility facade. Controller concerns live in controllerClient.ts and
// Node/Direct concerns live in nodeClient.ts. Keep this file thin so existing
// UI imports do not couple those two transports back together.

export {
  CloudSessionExpiredError,
  acceptOrganizationInvite,
  controllerUrl,
  createOrganization,
  exchangeCloudCode,
  fetchCloudIdentity,
  fetchCloudNodes,
  fetchOrganizations,
  forgetCloudNode,
  loadCloudSession,
  signOutCloud,
  startLogin,
  type CloudIdentity,
  type CloudNode,
  type CloudOrganization,
  type EffectivePlan,
  type OrganizationPlan,
  type OrganizationRole,
} from '@/lib/controllerClient';

import {
  loadDirectConnections,
  pairDirectNodeFromFragment,
  saveDirectConnection,
  type DirectProbeResult,
  type LocalConnection,
} from '@/lib/nodeClient';

export type { LocalConnection } from '@/lib/nodeClient';
export type LocalPairing = DirectProbeResult;

let cachedLaunchFragment: URLSearchParams | null | undefined;

export function consumeLaunchFragment(): URLSearchParams | null {
  if (cachedLaunchFragment !== undefined) return cachedLaunchFragment;
  if (!window.location.hash) return null;
  const params = new URLSearchParams(window.location.hash.slice(1));
  if (!params.get('action')) return null;
  window.history.replaceState(null, '', `${window.location.pathname}${window.location.search}`);
  cachedLaunchFragment = params;
  return params;
}

export function exchangeLocalPairing(params: URLSearchParams): Promise<DirectProbeResult> {
  return pairDirectNodeFromFragment(params);
}

// Pre-fleet compatibility: the old UI kept one preferred local connection.
// The fleet store is now authoritative; these wrappers can be removed once
// page.tsx no longer references the legacy single-Node surface.
export function saveLocalConnection(connection: LocalConnection): void {
  saveDirectConnection(connection);
}

export function loadLocalConnection(): LocalConnection | null {
  return Object.values(loadDirectConnections())[0] || null;
}

export function clearLocalConnection(): void {
  // The authoritative fleet entry is removed through forgetDirectConnection().
}

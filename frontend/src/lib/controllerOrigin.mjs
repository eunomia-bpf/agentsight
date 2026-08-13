// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

const PRODUCTION_CONTROLLER_URL = 'https://control.agentsight.us';
const PREVIEW_HOSTNAME = 'agentsight-preview.yunwei356.workers.dev';

/**
 * Keep the isolated Cloudflare preview on its own Controller, D1, and relay.
 * Explicit build-time overrides remain available for self-hosted deployments.
 */
export function resolveControllerUrl(configuredUrl, legacyUrl, location) {
  const override = configuredUrl || legacyUrl;
  if (override) return override.replace(/\/$/, '');
  if (location?.hostname === PREVIEW_HOSTNAME) return location.origin.replace(/\/$/, '');
  return PRODUCTION_CONTROLLER_URL;
}

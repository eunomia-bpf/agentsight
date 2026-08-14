// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

export const SUPPORTED_LOGIN_PROVIDERS = ['github', 'google'];

export function providerConfigured(configuredProviders, provider) {
  return configuredProviders?.includes(provider) === true;
}

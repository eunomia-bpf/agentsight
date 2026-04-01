// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

'use client';

import { useContext } from 'react';
import { I18nContext } from './context';

export function useTranslation() {
  return useContext(I18nContext);
}

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

'use client';

import { useTranslation } from '@/i18n';

export function LanguageSwitcher() {
  const { locale, setLocale } = useTranslation();

  return (
    <div className="flex rounded-lg border border-gray-200 p-1">
      <button
        onClick={() => setLocale('en')}
        className={`px-2 py-1 text-xs rounded-md transition-colors ${
          locale === 'en'
            ? 'bg-blue-600 text-white'
            : 'text-gray-600 hover:bg-gray-100'
        }`}
      >
        EN
      </button>
      <button
        onClick={() => setLocale('zh')}
        className={`px-2 py-1 text-xs rounded-md transition-colors ${
          locale === 'zh'
            ? 'bg-blue-600 text-white'
            : 'text-gray-600 hover:bg-gray-100'
        }`}
      >
        中文
      </button>
    </div>
  );
}

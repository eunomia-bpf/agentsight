// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

'use client';

import React, { createContext, useState, useEffect, useCallback } from 'react';
import { en } from './locales/en';
import { zh } from './locales/zh';

export type Locale = 'en' | 'zh';
export type TranslationKey = keyof typeof en;

type Translations = Record<TranslationKey, string>;

const locales: Record<Locale, Translations> = { en, zh };

export interface I18nContextType {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}

export const I18nContext = createContext<I18nContextType>({
  locale: 'en',
  setLocale: () => {},
  t: (key) => en[key],
});

function detectLocale(): Locale {
  if (typeof window === 'undefined') return 'en';

  const saved = localStorage.getItem('agentsight-locale');
  if (saved === 'en' || saved === 'zh') return saved;

  const browserLang = navigator.language;
  if (browserLang.startsWith('zh')) return 'zh';

  return 'en';
}

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>('en');

  useEffect(() => {
    setLocaleState(detectLocale());
  }, []);

  const setLocale = useCallback((newLocale: Locale) => {
    setLocaleState(newLocale);
    localStorage.setItem('agentsight-locale', newLocale);
    document.documentElement.lang = newLocale;
  }, []);

  useEffect(() => {
    document.documentElement.lang = locale;
  }, [locale]);

  const t = useCallback(
    (key: TranslationKey, params?: Record<string, string | number>): string => {
      let value = locales[locale][key] || locales['en'][key] || key;
      if (params) {
        Object.entries(params).forEach(([k, v]) => {
          value = value.replace(new RegExp(`\\{${k}\\}`, 'g'), String(v));
        });
      }
      return value;
    },
    [locale],
  );

  return (
    <I18nContext.Provider value={{ locale, setLocale, t }}>
      {children}
    </I18nContext.Provider>
  );
}

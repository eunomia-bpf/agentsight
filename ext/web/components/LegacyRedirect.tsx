'use client';

import { useEffect } from 'react';

export default function LegacyRedirect() {
  useEffect(() => {
    window.location.replace(`${process.env.NEXT_PUBLIC_BASE_PATH || ''}/`);
  }, []);
  return null;
}

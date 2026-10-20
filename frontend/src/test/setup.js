import { cleanup } from '@testing-library/react';
import { afterEach } from 'vitest';

import { setSystemDark } from './matchMedia';

// Every test starts with a light system, no cookies, nothing rendered and nothing set on <html>
afterEach(() => {
  cleanup();
  setSystemDark(false);
  const html = document.documentElement;
  delete html.dataset.theme;
  html.style.colorScheme = '';
  html.removeAttribute('lang');
  for (const cookie of document.cookie.split('; ').filter(Boolean)) {
    document.cookie = `${cookie.split('=')[0]}=; max-age=0; path=/`;
  }
});

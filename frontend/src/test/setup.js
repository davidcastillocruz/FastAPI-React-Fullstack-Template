import { cleanup } from '@testing-library/react';
import { afterEach } from 'vitest';

import { setSystemDark } from './matchMedia';

// Every test starts with a light system, no cookies and nothing rendered
afterEach(() => {
  cleanup();
  setSystemDark(false);
  for (const cookie of document.cookie.split('; ').filter(Boolean)) {
    document.cookie = `${cookie.split('=')[0]}=; max-age=0; path=/`;
  }
});

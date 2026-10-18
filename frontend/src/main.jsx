import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { createBrowserRouter, RouterProvider } from 'react-router';

import LanguageProvider from '@/languages/LanguageProvider';
import HomePage from '@/pages/HomePage/HomePage';
import ThemeProvider from '@/themes/ThemeProvider';
import { applyTheme, getInitialTheme } from '@/themes/theme';
import '@/themes/themes.css';
import '@/index.css';

// Every route of the app
const router = createBrowserRouter([
  { path: '/', element: <HomePage /> },
  // { path: '/about', element: <AboutPage /> },
]);

// Before the first render, so React never paints the page with the wrong theme
applyTheme(getInitialTheme());

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <ThemeProvider>
      <LanguageProvider>
        <RouterProvider router={router} />
      </LanguageProvider>
    </ThemeProvider>
  </StrictMode>,
);

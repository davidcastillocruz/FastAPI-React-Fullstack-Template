import { act, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, test, vi } from 'vitest';

import { getCookie, setCookie } from '@/utils/cookies';

import { getBrowserLanguage, getInitialLanguage, getSavedLanguage } from './languages';
import LanguageProvider from './LanguageProvider';
import { useLanguage } from './useLanguage';
import { useT } from './useT';

// Languages of the browser for one test
function browserLanguages(...tags) {
  vi.spyOn(navigator, 'languages', 'get').mockReturnValue(tags);
}

afterEach(() => vi.restoreAllMocks());

describe('language detection', () => {
  test('first language of the browser that we have, trying the base one too', () => {
    browserLanguages('fr-FR', 'es-ES', 'en');
    expect(getBrowserLanguage()).toBe('es');
  });

  test('a browser without any of our languages gets the main one', () => {
    browserLanguages('fr-FR', 'de');
    expect(getBrowserLanguage()).toBe('en');
  });

  test('a valid cookie wins over the browser', () => {
    browserLanguages('en');
    setCookie('language', 'es');
    expect(getInitialLanguage()).toBe('es');
  });

  test('an invalid cookie is deleted', () => {
    setCookie('language', 'fr');
    expect(getSavedLanguage()).toBeNull();
    expect(getCookie('language')).toBeNull();
  });
});

// Each test gets its own translations: useT checks every file only the first time it sees it
function Texts({ translations, keyName = 'greeting', args = { name: 'Ana' } }) {
  const t = useT(translations);
  const { setLanguage } = useLanguage();
  return (
    <>
      <p>{t(keyName, args)}</p>
      <button onClick={() => setLanguage('es')}>es</button>
      <button onClick={() => setLanguage('fr')}>fr</button>
    </>
  );
}

function renderTexts(props) {
  return render(
    <LanguageProvider>
      <Texts {...props} />
    </LanguageProvider>,
  );
}

const greeting = () => ({ greeting: { en: 'Hello {name}', es: 'Hola {name}' } });

describe('LanguageProvider and useT', () => {
  test('texts in the detected language, with the placeholders filled', () => {
    browserLanguages('es-ES');
    renderTexts({ translations: greeting() });
    expect(screen.getByText('Hola Ana')).toBeTruthy();
    expect(document.documentElement.lang).toBe('es');
  });

  test('setLanguage repaints the texts, saves the cookie and sets <html lang>', () => {
    browserLanguages('en');
    renderTexts({ translations: greeting() });
    expect(screen.getByText('Hello Ana')).toBeTruthy();

    act(() => screen.getByRole('button', { name: 'es' }).click());
    expect(screen.getByText('Hola Ana')).toBeTruthy();
    expect(getCookie('language')).toBe('es');
    expect(document.documentElement.lang).toBe('es');
  });

  test('an unknown language is ignored', () => {
    const error = vi.spyOn(console, 'error').mockImplementation(() => {});
    browserLanguages('en');
    renderTexts({ translations: greeting() });
    act(() => screen.getByRole('button', { name: 'fr' }).click());
    expect(screen.getByText('Hello Ana')).toBeTruthy();
    expect(getCookie('language')).toBeNull();
    expect(error).toHaveBeenCalledOnce();
  });

  test('a missing placeholder argument stays as it is', () => {
    browserLanguages('en');
    renderTexts({ translations: greeting(), args: {} });
    expect(screen.getByText('Hello {name}')).toBeTruthy();
  });

  test('a missing key shows the key and logs an error', () => {
    const error = vi.spyOn(console, 'error').mockImplementation(() => {});
    browserLanguages('en');
    renderTexts({ translations: greeting(), keyName: 'nope' });
    expect(screen.getByText('nope')).toBeTruthy();
    expect(error).toHaveBeenCalledWith('Translation "nope" not found');
  });

  test('a missing text falls back to the main language and the file check reports it', () => {
    const error = vi.spyOn(console, 'error').mockImplementation(() => {});
    browserLanguages('es');
    renderTexts({ translations: { greeting: { en: 'Hello {name}' } } });
    expect(screen.getByText('Hello Ana')).toBeTruthy();
    expect(error).toHaveBeenCalledWith('Translation "greeting" has no text in: es', expect.anything());
  });

  test('the file check reports different placeholders between languages', () => {
    const error = vi.spyOn(console, 'error').mockImplementation(() => {});
    browserLanguages('en');
    renderTexts({ translations: { greeting: { en: 'Hello {name}', es: 'Hola {nombre}' } } });
    expect(error).toHaveBeenCalledWith('Translation "greeting" has different {placeholders} in "es"', expect.anything());
  });

  test('useLanguage outside the provider fails with a clear error', () => {
    vi.spyOn(console, 'error').mockImplementation(() => {});
    expect(() => render(<Texts translations={greeting()} />)).toThrow('useLanguage must be used inside LanguageProvider');
  });
});

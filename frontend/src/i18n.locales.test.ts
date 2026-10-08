// Copyright (c) 2026 anonysec
// SPDX-License-Identifier: MIT

/** Locale lists: bot LOCALES, frontend lang files, SUPPORTED_LANGS — one set. */
import { describe, it, expect, vi } from 'vitest';
import { createElement } from 'react';
import { readFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';
import { render } from '@testing-library/react';

vi.mock('./services/api', () => ({
  default: { get: vi.fn(() => new Promise(() => {})) },
  apiBase: '/api',
  urlPath: '',
}));
vi.mock('./context/ThemeContext', () => ({
  useTheme: () => ({ theme: 'light', setTheme: () => {} }),
}));

import { SUPPORTED_LANGS, LANG_LABELS } from './i18n';
import AppearanceSection from './pages/settings/AppearanceSection';

const repoRoot = join(process.cwd(), '..');

const langFiles = readdirSync(join(repoRoot, 'frontend', 'src', 'lang'))
  .filter((f) => f.endsWith('.json'))
  .map((f) => f.replace(/\.json$/, ''))
  .sort();

describe('locale lists are single-sourced', () => {
  it('bot LOCALES matches the frontend lang files', () => {
    const py = readFileSync(join(repoRoot, 'backend', 'bot', 'i18n.py'), 'utf8');
    const tuple = py.match(/LOCALES\s*=\s*\(([^)]*)\)/);
    expect(tuple, 'backend/bot/i18n.py must declare LOCALES').toBeTruthy();
    const botLocales = [...tuple![1].matchAll(/["']([^"']+)["']/g)].map((m) => m[1]).sort();
    expect(botLocales).toEqual(langFiles);
  });

  it('SUPPORTED_LANGS matches the frontend lang files', () => {
    expect([...SUPPORTED_LANGS].sort()).toEqual(langFiles);
  });
});

describe('AppearanceSection renders from SUPPORTED_LANGS', () => {
  it('shows one button per supported language, labelled from LANG_LABELS', () => {
    render(createElement(AppearanceSection));
    const buttons = [...document.querySelectorAll('.sp-lang-btn')];
    expect(buttons).toHaveLength(SUPPORTED_LANGS.length);
    expect(buttons.map((b) => b.textContent)).toEqual(
      SUPPORTED_LANGS.map((code) => LANG_LABELS[code]),
    );
  });
});

describe('DashboardLayout does not own the stored language', () => {
  it("never touches localStorage['ovmanager-lang']", () => {
    const src = readFileSync(
      join(repoRoot, 'frontend', 'src', 'pages', 'DashboardLayout.tsx'),
      'utf8',
    );
    expect(src).not.toMatch(/localStorage\.(?:get|set)Item\(\s*['"]ovmanager-lang['"]/);
  });
});

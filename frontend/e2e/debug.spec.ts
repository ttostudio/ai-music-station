import { test, expect } from '@playwright/test';
import * as fs from 'fs';

test('debug: print page structure', async ({ page }) => {
  await page.goto('http://localhost:3200/');
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(3000);

  const info = await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button')).map((b) => ({
      class: b.className,
      text: (b.textContent || '').trim().substring(0, 50),
    }));
    const roles = Array.from(document.querySelectorAll('[role]')).map((el) => ({
      tag: el.tagName,
      role: el.getAttribute('role'),
      class: el.className.substring(0, 100),
    }));
    return { buttons, roles, bodySnippet: document.body.innerHTML.substring(0, 3000) };
  });

  fs.writeFileSync('/tmp/page-debug.json', JSON.stringify(info, null, 2));
  expect(info.buttons.length).toBeGreaterThanOrEqual(0);
});

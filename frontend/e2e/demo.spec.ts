// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

import { expect, test } from '@playwright/test';
import { mockController } from './fixtures';

test('recorded demo exposes overview, conversation, process, and analysis data', async ({ page }) => {
  await mockController(page);
  await page.goto('/');

  await page.getByRole('button', { name: 'Enter demo' }).click();
  await expect(page.getByText('Recorded demo').first()).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Agents on this machine' })).toBeVisible();
  await expect(page.getByText('18.6%').first()).toBeVisible();
  await expect(page.getByText('284 MB').first()).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Subscriptions' })).toBeVisible();
  await expect(page.getByText('63% remaining')).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Agent Plan' })).toBeVisible();
  await expect(page.getByText('Run browser regression coverage').first()).toBeVisible();

  await page.getByRole('button', { name: 'codex', exact: true }).click();
  await expect(page.getByRole('tab', { name: 'Conversation' })).toHaveAttribute('aria-selected', 'true');
  await expect(page.getByText(/recorded demo only loaded the snapshot/)).toBeVisible();

  await page.getByRole('tab', { name: 'Process tree & AI prompts' }).click();
  await expect(page.getByRole('heading', { name: 'Process Tree & AI Prompts' })).toBeVisible();
  await expect(page.getByText('codex', { exact: true }).first()).toBeVisible();

  await page.getByRole('tab', { name: 'Analysis' }).click();
  await expect(page.getByRole('heading', { name: 'Token usage' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Execution' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Resources & health' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Timeline View' })).toBeVisible();
});

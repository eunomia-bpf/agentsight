// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

import { expect, test, type Page } from '@playwright/test';
import { mockController } from './fixtures';

async function openLab(page: Page) {
  await expect(page.getByRole('heading', { name: 'Machine fleet' })).toBeVisible();
  await expect(page.getByRole('button', { name: /Online Lab workstation/ })).toBeVisible();
  await page.getByLabel('Machine view').selectOption('node-lab');
  await expect(page.getByRole('heading', { name: 'Agents on this machine' })).toBeVisible();
}

async function openCodexSession(page: Page) {
  await page.getByRole('button', { name: 'codex', exact: true }).click();
  await expect(page.getByRole('tab', { name: 'Conversation' })).toHaveAttribute('aria-selected', 'true');
  await expect(page.getByText('I will add browser tests.')).toBeVisible();
}

test('anonymous entry offers both sign-in providers, language switching, and the recorded demo', async ({ page }) => {
  await mockController(page);
  await page.addInitScript(() => window.localStorage.setItem('agentsight-locale', 'zh'));
  await page.goto('/');

  await expect(page.getByRole('dialog')).toBeVisible();
  await expect(page.getByRole('heading', { name: '打开你的 AgentSight 数据' })).toBeVisible();
  await expect(page.getByRole('button', { name: '使用 GitHub 继续' })).toBeVisible();
  await expect(page.getByRole('button', { name: '使用 Google 继续' })).toBeVisible();
  await page.getByRole('button', { name: '进入演示' }).click();
  await expect(page.getByText('录制演示').first()).toBeVisible();
  await expect(page.getByRole('heading', { name: '当前机器上的 Agent' })).toBeVisible();
});

test('signed-in user opens a relay Node and sees machine value before session detail', async ({ page }) => {
  await mockController(page, { signedIn: true });
  await page.goto('/');

  await expect(page.getByLabel('Machine view')).toHaveValue('all');
  await page.getByRole('button', { name: 'Unreachable 1' }).click();
  await expect(page.getByRole('button', { name: /Unreachable Offline laptop/ })).toBeVisible();
  await expect(page.getByRole('button', { name: /Online Lab workstation/ })).toHaveCount(0);
  await page.getByRole('button', { name: 'All 2' }).click();
  await openLab(page);

  await page.getByRole('button', { name: '中文' }).click();
  await expect(page.getByRole('heading', { name: '当前机器上的 Agent' })).toBeVisible();
  await page.getByRole('button', { name: 'EN', exact: true }).click();

  await expect(page.getByText('Running').first()).toBeVisible();
  await expect(page.getByText('2.4k').first()).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Subscriptions' })).toBeVisible();
  await expect(page.getByText('65% remaining')).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Agent Plan' })).toBeVisible();
  await expect(page.getByText('Verify conversation and analysis').first()).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Machine resources' })).toBeVisible();
});

test('conversation, message send, process tree, timeline filters, and event detail work together', async ({ page }) => {
  const state = await mockController(page, { signedIn: true });
  await page.goto('/');
  await openLab(page);
  await openCodexSession(page);

  const composer = page.getByPlaceholder('Send a follow-up to this session…');
  await composer.fill('Run the final browser regression suite.');
  await page.getByRole('button', { name: 'Send' }).click();
  await expect.poll(() => state.messages.length).toBe(1);
  expect(state.messages[0]).toEqual({ message: 'Run the final browser regression suite.' });
  await expect(composer).toHaveValue('');

  await page.getByRole('tab', { name: 'Process tree & AI prompts' }).click();
  await expect(page.getByRole('heading', { name: 'Process Tree & AI Prompts' })).toBeVisible();
  await expect(page.getByText('codex', { exact: true }).first()).toBeVisible();

  await page.getByRole('tab', { name: 'Analysis' }).click();
  await expect(page.getByRole('heading', { name: 'Token usage' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Execution' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Resources & health' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Timeline View' })).toBeVisible();
  const panel = page.getByRole('tabpanel');
  await panel.getByRole('combobox').first().selectOption('file');
  await panel.locator('.cursor-pointer').first().click();
  await expect(page.getByRole('heading', { name: 'Timeline Event Details' })).toBeVisible();
  await expect(page.getByText('file-1', { exact: true })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Raw Data' })).toBeVisible();
});

test('unsafe message resume is blocked and disables further sends', async ({ page }) => {
  await mockController(page, { signedIn: true, blockMessages: true });
  await page.goto('/');
  await openLab(page);
  await openCodexSession(page);

  const composer = page.getByPlaceholder('Send a follow-up to this session…');
  await composer.fill('Continue this session.');
  await page.getByRole('button', { name: 'Send' }).click();
  await expect(page.getByText(/already running in another agent process/)).toBeVisible();
  await expect(page.getByPlaceholder('This session is read-only.')).toBeDisabled();
});

test('sign-out during initial Node loading returns to the anonymous entry', async ({ page }) => {
  const state = await mockController(page, { signedIn: true, nodeListDelayMs: 500 });
  await page.goto('/');
  await page.getByRole('button', { name: 'Nodes' }).click();
  await page.getByRole('dialog', { name: 'Your Nodes' }).getByRole('button', { name: 'Sign out' }).click();

  await expect(page.getByRole('heading', { name: 'Open your AgentSight data' })).toBeVisible();
  await expect.poll(() => state.signOuts).toBe(1);
});

test('Node management refresh, Direct setup, organization creation, sign-out, and mobile layout remain usable', async ({ page }) => {
  const state = await mockController(page, { signedIn: true });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/');
  await page.getByRole('button', { name: 'Nodes' }).click();
  const manager = page.getByRole('dialog', { name: 'Your Nodes' });
  await expect(manager).toBeVisible();

  const offline = manager.getByRole('article').filter({ hasText: 'Offline laptop' });
  await offline.getByRole('button', { name: 'Connect Direct' }).click();
  await expect(page.getByLabel('Direct URL or IP')).toBeVisible();
  await expect(page.getByLabel('Node bootstrap key')).toBeVisible();
  await manager.getByRole('button', { name: 'Cancel Direct' }).click();

  const beforeRefresh = state.nodeListRequests;
  await manager.getByRole('button', { name: 'Refresh' }).click();
  await expect.poll(() => state.nodeListRequests).toBeGreaterThan(beforeRefresh);

  await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.setViewportSize({ width: 1280, height: 900 });
  await manager.getByRole('button', { name: 'Close Node manager' }).click();
  await page.getByRole('button', { name: '+ Organization' }).click();
  await page.getByLabel('Organization name').fill('Browser Test Team');
  await page.getByRole('button', { name: 'Create', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Machine fleet' })).toBeVisible();

  await page.getByRole('button', { name: 'Nodes' }).click();
  await page.getByRole('dialog', { name: 'Your Nodes' }).getByRole('button', { name: 'Sign out' }).click();
  await expect(page.getByRole('heading', { name: 'Open your AgentSight data' })).toBeVisible();
  await expect.poll(() => state.signOuts).toBe(1);
});

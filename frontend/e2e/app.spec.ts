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
  await expect(page.getByRole('link', { name: '服务条款' })).toHaveAttribute('href', '/terms/');
  await expect(page.getByRole('link', { name: '隐私政策' })).toHaveAttribute('href', '/privacy/');
  await page.getByRole('button', { name: '进入演示' }).click();
  await expect(page.getByText('录制演示').first()).toBeVisible();
  await expect(page.getByRole('heading', { name: '当前机器上的 Agent' })).toBeVisible();
});

test('signed-in user opens a relay Node and sees machine value before session detail', async ({ page }) => {
  await mockController(page, { signedIn: true });
  await page.goto('/');

  await expect(page.getByLabel('Machine view')).toHaveValue('all');
  await expect(page.getByText('2/3', { exact: true })).toBeVisible();
  await expect(page.getByText('3.0k', { exact: true })).toBeVisible();
  await expect(page.getByText('80% remaining')).toBeVisible();
  await page.getByRole('button', { name: 'Unreachable 1' }).click();
  await expect(page.getByRole('button', { name: /Unreachable Offline laptop/ })).toBeVisible();
  await expect(page.getByRole('button', { name: /Online Lab workstation/ })).toHaveCount(0);
  await page.getByRole('button', { name: 'All 3' }).click();
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

test('signed-in user explicitly links Google without email-based account merging', async ({ page }) => {
  const state = await mockController(page, { signedIn: true });
  await page.goto('/');
  await page.getByRole('button', { name: 'Nodes' }).click();
  await expect(page.getByRole('button', { name: 'Link Google' })).toBeVisible();
  await page.getByRole('button', { name: 'Link Google' }).click();
  await expect.poll(() => state.accountLinks.length).toBe(1);
  expect(state.accountLinks[0].provider).toBe('google');
  expect(state.accountLinks[0].code_challenge).toMatch(/^[A-Za-z0-9_-]{43}$/);
  await expect(page).toHaveURL(/accounts\.google\.com\/o\/oauth2\/v2\/auth/);
});

test('public privacy and terms pages describe the hosted data boundary', async ({ page }) => {
  await page.goto('/privacy/');
  await expect(page.getByRole('heading', { name: 'Privacy Policy' })).toBeVisible();
  await expect(page.getByText('does not persist Node snapshots')).toBeVisible();
  await page.goto('/terms/');
  await expect(page.getByRole('heading', { name: 'Terms of Service' })).toBeVisible();
  await expect(page.getByText('Only connect machines and inspect sessions')).toBeVisible();
});

test('organization owner can open Pro Checkout and the Stripe billing portal', async ({ page }) => {
  const state = await mockController(page, { signedIn: true, billingStatus: 'inactive' });
  await page.goto('/');

  await expect(page.getByRole('button', { name: '$5 monthly' })).toBeVisible();
  await expect(page.getByRole('button', { name: '$49 yearly' })).toBeVisible();
  await page.getByRole('button', { name: '$5 monthly' }).click();
  await expect.poll(() => state.billingCheckouts).toEqual([{ plan: 'pro', interval: 'monthly' }]);
  await expect(page).toHaveURL('https://checkout.stripe.com/c/pay/browser-test');

  state.billingStatus = 'active';
  state.contributorPro = true;
  await page.goto('/');
  await page.getByRole('button', { name: 'Manage billing' }).click();
  await expect.poll(() => state.billingPortalRequests).toBe(1);
  await expect(page).toHaveURL('https://billing.stripe.com/p/session/browser-test');
});

test('billing controls fail closed when Stripe is unavailable', async ({ page }) => {
  await mockController(page, {
    signedIn: true, billingStatus: 'inactive', checkoutAvailable: false,
  });
  await page.goto('/');

  await expect(page.getByText('Paid checkout is not configured for this deployment.')).toBeVisible();
  await expect(page.getByRole('button', { name: '$5 monthly' })).toHaveCount(0);
  await expect(page.getByRole('button', { name: '$49 yearly' })).toHaveCount(0);

  await page.goto('/?billing=canceled');
  await expect(page.getByText('Checkout was canceled. No subscription change was made.')).toBeVisible();
  await expect(page).toHaveURL('/');
});

test('conversation, message send, process tree, timeline filters, and event detail work together', async ({ page }) => {
  const state = await mockController(page, { signedIn: true, responseDelayMs: 10_500 });
  await page.goto('/');
  await openLab(page);
  await openCodexSession(page);

  const composer = page.getByPlaceholder('Send a follow-up to this session…');
  await composer.fill('Run the final browser regression suite.');
  await page.getByRole('button', { name: 'Send' }).click();
  await expect.poll(() => state.messages.length).toBe(1);
  expect(state.messages[0]).toEqual({ message: 'Run the final browser regression suite.' });
  await expect(composer).toHaveValue('');
  await expect(composer).toBeEnabled();
  await expect(page.getByRole('button', { name: 'Send' })).toBeVisible();
  await expect(page.getByText('Browser follow-up complete.')).toBeVisible({ timeout: 25_000 });

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
  await page.setViewportSize({ width: 390, height: 844 });
  await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
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
  await expect(page.getByRole('heading', { name: 'Machine fleet' })).toBeVisible();
  await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.getByRole('button', { name: 'Nodes' }).click();
  const manager = page.getByRole('dialog', { name: 'Your Nodes' });
  await expect(manager).toBeVisible();

  const offline = manager.getByRole('article').filter({ hasText: 'Offline laptop' });
  await offline.getByRole('button', { name: 'Connect Direct' }).click();
  await page.getByLabel('Direct URL or IP').fill('http://node-direct.test:7395');
  await page.getByLabel('Node bootstrap key').fill('a'.repeat(40));
  await manager.getByRole('button', { name: 'Pair and connect' }).click();
  await expect(page.getByRole('heading', { name: 'Agents on this machine' })).toBeVisible();
  await expect.poll(() => state.directRequests).toEqual([
    'GET /api/v1/info', 'POST /api/v1/capabilities',
    'GET /api/v1/snapshot', 'GET /api/v1/overview',
  ]);
  await expect.poll(() => state.registrations.length).toBe(1);
  expect(state.registrations[0]).toMatchObject({ id: 'node-offline', organization_id: 'org-personal' });
  await page.getByLabel('Machine view').selectOption('all');
  await expect(page.getByRole('heading', { name: 'Machine fleet' })).toBeVisible();

  const beforeRefresh = state.nodeListRequests;
  await page.getByRole('button', { name: 'Nodes' }).click();
  const refreshedManager = page.getByRole('dialog', { name: 'Your Nodes' });
  await refreshedManager.getByRole('button', { name: 'Refresh' }).click();
  await expect.poll(() => state.nodeListRequests).toBeGreaterThan(beforeRefresh);

  page.once('dialog', (dialog) => dialog.accept());
  await refreshedManager.getByRole('article').filter({ hasText: 'Offline laptop' })
    .getByRole('button', { name: 'Remove', exact: true }).click();
  await expect.poll(() => state.deletedNodes).toContain('node-offline');

  await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.setViewportSize({ width: 1280, height: 900 });
  await refreshedManager.getByRole('button', { name: 'Close Node manager' }).click();
  await page.getByRole('button', { name: '+ Organization' }).click();
  await page.getByLabel('Organization name').fill('Browser Test Team');
  await page.getByRole('button', { name: 'Create', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Machine fleet' })).toBeVisible();
  await expect.poll(() => state.organizations).toEqual([{ name: 'Browser Test Team' }]);
  await expect(page.locator('header select').first()).toHaveValue('org-team');
  await expect(page.getByText('Team is $10 per member monthly.')).toBeVisible();

  await page.getByRole('button', { name: 'Nodes' }).click();
  await page.getByRole('dialog', { name: 'Your Nodes' }).getByRole('button', { name: 'Sign out' }).click();
  await expect(page.getByRole('heading', { name: 'Open your AgentSight data' })).toBeVisible();
  await expect.poll(() => state.signOuts).toBe(1);
});

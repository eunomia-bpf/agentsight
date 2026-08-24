// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

import type { Page, Route } from '@playwright/test';

const started = 1_780_000_000_000;
const sessionId = 'codex-thread-1';

export const snapshot = {
  schema_version: 1,
  summary: {
    source: 'live', view_events: 12, sessions: 2, total_tokens: 2_400,
    start_timestamp_ms: started, end_timestamp_ms: started + 60_000,
  },
  sessions: [
    {
      id: 'session-codex', agent_type: 'codex', start_timestamp_ms: started,
      end_timestamp_ms: null, status: 'running', model: 'gpt-5',
      input_tokens: 1_200, output_tokens: 300, total_tokens: 1_500,
      attributes: {
        session_id: sessionId, display_id: 'codex:thread-1', cwd: '/workspace/agentsight',
        prompt_preview: 'Implement browser regression coverage',
        last_message_at: '2026-08-13T18:00:00Z',
        usage: { input_tokens: 1_200, output_tokens: 300, cache_read_tokens: 500, total_tokens: 2_000 },
        plan: [
          { step: 'Cover the signed-in dashboard', status: 'completed' },
          { step: 'Verify conversation and analysis', status: 'in_progress' },
        ],
        subscription: {
          provider: 'codex', observed_at: '2026-08-13T18:00:00Z', plan_type: 'pro',
          primary: { used_percent: 35, window_minutes: 300, resets_at: 4_102_444_800 },
        },
      },
    },
    {
      id: 'session-claude', agent_type: 'claude', start_timestamp_ms: started - 120_000,
      end_timestamp_ms: started - 60_000, status: 'stopped', model: 'claude-sonnet',
      input_tokens: 700, output_tokens: 200, total_tokens: 900,
      attributes: { session_id: 'claude-thread-1', cwd: '/workspace/other', prompt_preview: 'Review the change' },
    },
  ],
  tool_calls: [{
    id: 'tool-1', session_id: sessionId, timestamp_ms: started + 20_000,
    tool_name: 'exec', status: 'success', related_pid: 101,
  }],
  process_nodes: [
    {
      id: 'process-root', pid: 101, ppid: 1, start_timestamp_ms: started,
      end_timestamp_ms: null, comm: 'codex', command: 'codex', status: 'running',
    },
    {
      id: 'process-child', pid: 102, ppid: 101, start_timestamp_ms: started + 10_000,
      end_timestamp_ms: started + 30_000, comm: 'git', command: 'git diff', status: 'success',
    },
  ],
  audit_events: [
    {
      id: 'prompt-1', timestamp_ms: started + 5_000, audit_type: 'llm', pid: 101,
      comm: 'codex', action: 'request', subject: 'gpt-5', status: 'success',
      summary: 'Implement browser regression coverage', details: { prompt: 'Implement browser regression coverage' },
    },
    {
      id: 'response-1', timestamp_ms: started + 8_000, audit_type: 'llm', pid: 101,
      comm: 'codex', action: 'response', subject: 'gpt-5', status: 'success',
      summary: 'I will add browser tests', details: { response: 'I will add browser tests' },
    },
    {
      id: 'file-1', timestamp_ms: started + 22_000, audit_type: 'file', pid: 101,
      comm: 'codex', action: 'write', target: '/workspace/agentsight/frontend/e2e/app.spec.ts',
      status: 'success', summary: 'write frontend/e2e/app.spec.ts',
    },
  ],
  resource_samples: [
    { timestamp_ms: started + 12_000, pid: 101, comm: 'codex', cpu_percent: 8, rss_mb: 120 },
    { timestamp_ms: started + 24_000, pid: 101, comm: 'codex', cpu_percent: 12, rss_mb: 140 },
  ],
  network_targets: [{
    pid: 101, comm: 'codex', host: 'api.openai.com', path: '/v1/responses', count: 2,
    error_count: 0, first_timestamp_ms: started + 5_000, last_timestamp_ms: started + 8_000,
  }],
};

export const overview = {
  mode: 'live', total_tokens: 2_400, failures: [], notes: [],
  rows: [{
    session_id: sessionId, session: 'codex:thread-1', agent: 'codex', pid: 101,
    model: 'gpt-5', age_s: 2, cpu_percent: 12, rss_mb: 140, processes: 2,
    tokens: 1_500, tools: 1, execs: 1, failures: 0, files: 1, network: 1,
    trace: 'agent-native+proc', command: 'Implement browser regression coverage',
    workspace: '/workspace/agentsight', last_message_at: '2026-08-13T18:00:00Z',
    process_details: [
      { pid: 101, ppid: 1, start_timestamp_ms: started, comm: 'codex', command: 'codex', cwd: '/workspace/agentsight', cpu_percent: 8, rss_mb: 120 },
      { pid: 102, ppid: 101, start_timestamp_ms: started + 10_000, comm: 'git', command: 'git diff', cwd: '/workspace/agentsight', cpu_percent: 4, rss_mb: 20 },
    ],
    plan: [{ step: 'Verify conversation and analysis', status: 'in_progress' }],
    subscription: snapshot.sessions[0].attributes.subscription,
  }],
};

export const studioOverview = {
  mode: 'live', total_tokens: 600, failures: [], notes: [],
  rows: [{
    session_id: 'claude-studio-1', session: 'claude:studio-1', agent: 'claude', pid: 201,
    model: 'claude-sonnet', age_s: 4, cpu_percent: 4, rss_mb: 60, processes: 1,
    tokens: 600, tools: 0, execs: 0, failures: 0, files: 0, network: 1,
    trace: 'agent-native+proc', command: 'Review fleet aggregation', workspace: '/workspace/studio',
    last_message_at: '2026-08-13T18:05:00Z', process_details: [], plan: [],
    subscription: {
      provider: 'codex', observed_at: '2026-08-13T18:05:00Z', plan_type: 'pro',
      primary: { used_percent: 20, window_minutes: 300, resets_at: 4_102_444_800 },
    },
  }],
};

export const sessionDetail = {
  session_id: sessionId, agent_type: 'codex', model: 'gpt-5', cwd: '/workspace/agentsight',
  duration_ms: 60_000,
  usage: { input_tokens: 1_200, output_tokens: 300, cache_read_tokens: 500, total_tokens: 2_000 },
  model_usage: { 'gpt-5': { input_tokens: 1_200, output_tokens: 300, total_tokens: 1_500 } },
  tools: { exec: 1 }, files: { 'frontend/e2e/app.spec.ts': 1 },
  events: {
    prompts: [{ ts_ms: started + 5_000, text: 'Implement browser regression coverage' }],
    llm_responses: [{ ts_ms: started + 8_000, text: 'I will add browser tests.', model: 'gpt-5', total_tokens: 1_500 }],
    tools: [{ ts_ms: started + 20_000, tool_name: 'exec', status: 'success', command: 'npm test' }],
    plan: [
      { step: 'Cover the signed-in dashboard', status: 'completed' },
      { step: 'Verify conversation and analysis', status: 'in_progress' },
    ],
  },
};

export const nodes = [
  {
    id: 'node-lab', organization_id: 'org-personal', name: 'Lab workstation', version: '1.0.18',
    connection_mode: 'relay', has_direct_config: false, last_seen_at: 1_780_000_000, created_at: 1_779_000_000,
  },
  {
    id: 'node-offline', organization_id: 'org-personal', name: 'Offline laptop', version: '1.0.17',
    connection_mode: 'direct', has_direct_config: false, last_seen_at: 1_779_000_000, created_at: 1_778_000_000,
  },
  {
    id: 'node-studio', organization_id: 'org-personal', name: 'Studio workstation', version: '1.0.18',
    connection_mode: 'relay', has_direct_config: false, last_seen_at: 1_780_000_100, created_at: 1_779_000_100,
  },
];

export interface MockState {
  messages: unknown[];
  messageAcceptedAt: number | null;
  nodeListRequests: number;
  deletedNodes: string[];
  signOuts: number;
  blockMessages: boolean;
  organizations: unknown[];
  registrations: unknown[];
  directRequests: string[];
}

function json(route: Route, body: unknown, status = 200) {
  return route.fulfill({
    status,
    contentType: 'application/json',
    headers: { 'Access-Control-Allow-Origin': '*' },
    body: JSON.stringify(body),
  });
}

export async function mockEmbeddedProbe(page: Page) {
  await page.route('http://127.0.0.1:4173/api/v1/info', (route) => route.fulfill({ status: 404 }));
}

export async function mockController(page: Page, options: {
  signedIn?: boolean;
  blockMessages?: boolean;
  nodeListDelayMs?: number;
  responseDelayMs?: number;
} = {}) {
  const state: MockState = {
    messages: [], nodeListRequests: 0, deletedNodes: [], signOuts: 0,
    messageAcceptedAt: null,
    blockMessages: options.blockMessages ?? false, organizations: [], registrations: [], directRequests: [],
  };
  await mockEmbeddedProbe(page);
  if (options.signedIn) {
    await page.addInitScript(() => {
      window.localStorage.setItem('agentsight.cloud-session.v1', 'browser-test-session');
      window.localStorage.setItem('agentsight-locale', 'en');
    });
  }
  await page.route('http://node-direct.test:7395/**', async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    state.directRequests.push(`${request.method()} ${path}`);
    const expected = path === '/api/v1/info' || path === '/api/v1/capabilities'
      ? `Bearer ${'a'.repeat(40)}` : `Bearer ${'b'.repeat(40)}`;
    if (request.headers().authorization !== expected) return json(route, { error: 'unauthorized' }, 401);
    if (path === '/api/v1/info') {
      return json(route, { node: { id: 'node-offline', name: 'Offline laptop', version: '1.0.18' } });
    }
    if (path === '/api/v1/capabilities') return json(route, { access_token: 'b'.repeat(40) });
    if (path === '/api/v1/snapshot') return json(route, snapshot);
    if (path === '/api/v1/overview') return json(route, overview);
    return json(route, { error: `Unhandled Direct route: ${request.method()} ${path}` }, 500);
  });
  await page.route('https://control.agentsight.us/**', async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const path = url.pathname;
    if (request.method() === 'OPTIONS') {
      await route.fulfill({
        status: 204,
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Headers': 'Authorization, Content-Type',
          'Access-Control-Allow-Methods': 'GET, POST, DELETE, OPTIONS',
        },
      });
      return;
    }
    if (path === '/v1/auth/providers') return json(route, { providers: ['github', 'google'] });
    if (request.headers().authorization !== 'Bearer browser-test-session') {
      return json(route, { error: 'missing_browser_test_authorization' }, 401);
    }
    if (path === '/v1/me') return json(route, { id: 'user-1', email: 'owner@example.com', name: 'Test Owner', provider: 'github' });
    if (path === '/v1/auth/logout') {
      state.signOuts += 1;
      return json(route, { ok: true });
    }
    if (path === '/v1/organizations' && request.method() === 'POST') {
      state.organizations.push(request.postDataJSON());
      return json(route, { organization: {
        id: 'org-team', name: 'Browser Test Team', kind: 'team', role: 'owner', plan: 'team',
        effectivePlan: 'team', billingInterval: null, billingStatus: 'inactive',
        currentPeriodEnd: null, contributorPro: false, createdAt: 1_780_000_000,
      } });
    }
    if (path === '/v1/organizations') return json(route, { organizations: [{
      id: 'org-personal', name: 'Test Owner', kind: 'personal', role: 'owner', plan: 'pro',
      effectivePlan: 'pro', billingInterval: 'monthly', billingStatus: 'active',
      currentPeriodEnd: 4_102_444_800, contributorPro: false, createdAt: 1_779_000_000,
    }] });
    if (path === '/v1/nodes' && request.method() === 'GET') {
      state.nodeListRequests += 1;
      if (options.nodeListDelayMs) {
        await new Promise((resolve) => setTimeout(resolve, options.nodeListDelayMs));
      }
      return json(route, { nodes: url.searchParams.get('organization_id') === 'org-team'
        ? [] : nodes.filter((node) => !state.deletedNodes.includes(node.id)) });
    }
    if (path === '/v1/nodes' && request.method() === 'POST') {
      state.registrations.push(request.postDataJSON());
      return json(route, { ok: true });
    }
    const status = path.match(/^\/v1\/nodes\/([^/]+)\/relay\/status$/);
    if (status) return json(route, { online: decodeURIComponent(status[1]) !== 'node-offline' });
    const relay = path.match(/^\/v1\/nodes\/([^/]+)\/relay(\/.*)$/);
    if (relay) {
      const nodeId = decodeURIComponent(relay[1]);
      const suffix = relay[2];
      if (nodeId === 'node-offline') return json(route, { error: 'relay_offline' }, 503);
      if (suffix === '/overview') return json(route, nodeId === 'node-studio' ? studioOverview : overview);
      if (suffix === '/snapshot') return json(route, snapshot);
      if (/^\/sessions\/[^/]+\/messages$/.test(suffix) && request.method() === 'POST') {
        state.messages.push(request.postDataJSON());
        if (state.blockMessages) {
          return json(route, { detail: 'This session is running outside AgentSight.' }, 409);
        }
        state.messageAcceptedAt = Date.now();
        return json(route, { accepted: true }, 202);
      }
      if (/^\/sessions\/[^/]+$/.test(suffix)) {
        const completed = state.messageAcceptedAt !== null
          && Date.now() - state.messageAcceptedAt >= (options.responseDelayMs ?? 700);
        if (!completed) return json(route, sessionDetail);
        const submitted = state.messages.at(-1) as { message?: string } | undefined;
        return json(route, {
          ...sessionDetail,
          events: {
            ...sessionDetail.events,
            prompts: [
              ...sessionDetail.events.prompts,
              { ts_ms: started + 70_000, text: submitted?.message || 'Follow-up' },
            ],
            llm_responses: [
              ...sessionDetail.events.llm_responses,
              { ts_ms: started + 71_000, text: 'Browser follow-up complete.', model: 'gpt-5' },
            ],
          },
        });
      }
    }
    const deletion = path.match(/^\/v1\/nodes\/([^/]+)$/);
    if (deletion && request.method() === 'DELETE') {
      state.deletedNodes.push(decodeURIComponent(deletion[1]));
      return json(route, { ok: true });
    }
    if (/^\/v1\/nodes\/[^/]+\/direct$/.test(path) && request.method() === 'DELETE') {
      return json(route, { ok: true });
    }
    return json(route, { error: `Unhandled browser-test route: ${request.method()} ${path}` }, 500);
  });
  return state;
}

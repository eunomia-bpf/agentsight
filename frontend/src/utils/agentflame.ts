import { AgentFlameReport } from '@/types/agentflame';

export async function fetchAgentFlameReport(basePath = ''): Promise<AgentFlameReport | null> {
  const response = await fetch(`${basePath}/api/v1/agentflame`);
  if (!response.ok) return null;
  return await response.json() as AgentFlameReport;
}

export async function fetchAgentFlameArtifactText(basePath: string, relative: string): Promise<string> {
  const encoded = relative.split('/').map(encodeURIComponent).join('/');
  const response = await fetch(`${basePath}/api/v1/agentflame/artifacts/${encoded}`);
  if (!response.ok) throw new Error(`agentflame artifact ${relative} returned ${response.status}`);
  return await response.text();
}

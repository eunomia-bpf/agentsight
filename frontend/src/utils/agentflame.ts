import { AgentFlameReport } from '@/types/agentflame';

export async function fetchAgentFlameReport(basePath = ''): Promise<AgentFlameReport | null> {
  const response = await fetch(`${basePath}/api/v1/agentflame`);
  if (!response.ok) return null;
  return await response.json() as AgentFlameReport;
}

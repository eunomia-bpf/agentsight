export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  tokens: number;
  timestamp: number;
  type?: 'text' | 'code' | 'tool_call' | 'tool_result';
  eventType?: 'request' | 'response' | 'command';
}

export interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  totalTokens: number;
  inputTokens: number;
  outputTokens: number;
  model: string;
  createdAt: number;
  updatedAt: number;
}

export interface TokenStats {
  total: number;
  byRole: Record<string, number>;
  byType: Record<string, number>;
  byMessage: Array<{ id: string; tokens: number; percentage: number }>;
}

// ==================== ChatML Token Breakdown Types ====================

/** ChatML Token 分解树节点 */
export interface TokenBreakdownNode {
  name: string;
  label: string;
  tokens: number;
  percentage: number;
  char_count: number;
  segment_type?: string;
  children?: TokenBreakdownNode[];
  items?: MessageItem[];
}

/** 对话消息明细 */
export interface MessageItem {
  index: number;
  tokens: number;
  is_history: boolean;
  content: string;
}

/** 完整 ChatML Token 分解结果 */
export interface ChatMLTokenBreakdown {
  file_path: string;
  model_name: string;
  total_tokens: number;
  blocks: TokenBreakdownNode[];
}

// ==================== Execution Trace Types ====================

/** 执行轨迹条目类型 */
export type TraceEntryType = 
  | 'assistant_text' 
  | 'assistant_skill' 
  | 'assistant_bash' 
  | 'assistant_read'
  | 'tool_result' 
  | 'user_message';

/** 执行轨迹条目 */
export interface TraceEntry {
  id: string;
  type: TraceEntryType;
  role: 'assistant' | 'user' | 'tool';
  title: string;
  subtitle?: string;
  content: string;
  tokens: number;
  isHistory: boolean;
  timestamp?: number;
  metadata?: {
    skillName?: string;
    command?: string;
    filePath?: string;
  };
}

/** 执行轨迹分组 */
export interface TraceGroup {
  id: string;
  title: string;
  entries: TraceEntry[];
  totalTokens: number;
}

// ==================== Trace Event Types ====================

/** Trace 事件子项 */
export interface TraceEventChild {
  name: string;
  label: string;
  tokens: number;
  percentage: number;
  char_count: number;
  content?: string;
  is_history?: boolean;
  response_items?: Array<{
    index: number;
    tokens: number;
    char_count: number;
    content: string;
  }>;
}

/** 分类统计项 */
export interface SummaryCategory {
  count: number;
  tokens: number;
  percentage: number;
}

/** Event 内嵌 summary（by_role + by_history 嵌套结构）*/
export interface EventSummary {
  by_role?: Record<string, SummaryCategory>;
  by_history?: Record<string, SummaryCategory>;
}

/** Trace 事件 */
export interface TraceEvent {
  type: 'request' | 'response' | 'toolcall';
  label: string;
  tokens: number;
  percentage: number;
  char_count: number;
  summary?: EventSummary;
  children: TraceEventChild[] | null;
  /** toolcall 类型特有字段 */
  cmdline?: string;
  stdout?: string;
  stderr?: string;
}

/** 根级分组统计（input/output 各含 by_role + by_history）*/
export interface GroupedSummary {
  tokens: number;
  percentage: number;
  by_role?: Record<string, SummaryCategory>;
  by_history?: Record<string, SummaryCategory>;
}

/** Trace 数据根结构 */
export interface TraceData {
  file_path?: string;
  model_name: string;
  total_tokens: number;
  summary?: {
    input?: GroupedSummary;
    output?: GroupedSummary;
    /** 兼容旧格式 */
    by_history?: Record<string, SummaryCategory>;
    by_role?: Record<string, SummaryCategory>;
  };
  events: TraceEvent[];
}

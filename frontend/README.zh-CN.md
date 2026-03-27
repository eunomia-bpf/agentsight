# AgentSight 前端

[English](README.md) | **中文**

基于 React/TypeScript 的现代 Web 界面，用于可视化 AgentSight collector 采集的 AI 智能体可观测性数据。提供交互式时间线视图、进程树和实时事件流。

## 概述

AgentSight 前端提供以下数据的直观可视化：

- **SSL/TLS 流量**：HTTP 请求、响应和加密通信
- **进程事件**：生命周期追踪、文件操作和系统调用
- **智能体行为**：智能体交互和系统活动的组合视图
- **实时数据**：智能体操作的实时流式传输和分析

## 功能特性

### 时间线视图
- 交互式事件时间线，支持缩放和平移
- 按类型、来源和进程分组事件
- 实时过滤和搜索功能
- 小地图导航，适用于大数据集
- 导出功能用于分析

### 进程树视图
- 进程关系的层级可视化
- 生命周期追踪（fork、exec、exit 事件）
- 资源使用监控和指标
- 父子关系映射
- 交互式节点展开和过滤

### 日志视图
- 原始事件检查，支持 JSON 格式化
- 语法高亮和美化打印
- 高级过滤和搜索
- 错误检测和验证
- 导出功能（JSON、CSV）

## 技术栈

- **框架**：Next.js 15+ with React 18+
- **语言**：TypeScript 5+，严格类型
- **样式**：Tailwind CSS，响应式设计
- **状态管理**：React hooks 和 context
- **数据处理**：实时日志解析和事件关联

## 快速开始

### 前置要求

- **Node.js**：18+ 或 20+（推荐）
- **npm**：9+ 或 yarn/pnpm
- **AgentSight Collector**：运行中，作为数据源

### 安装

```bash
# 克隆仓库
git clone https://github.com/eunomia-bpf/agentsight.git --recursive
cd agentsight/frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 打开浏览器
open http://localhost:3000
```

### 生产环境构建

```bash
# 构建生产版本
npm run build

# 启动生产服务器
npm start

# 或通过 collector 提供服务（推荐）
cd ../collector && cargo run server
# 访问 http://localhost:7395
```

## 使用方法

### 数据加载

前端支持多种数据输入方式：

#### 1. 实时流式传输（推荐）
```bash
# 以服务器模式启动 collector
cd ../collector && cargo run server

# 访问带实时数据的 Web 界面
open http://localhost:7395/timeline
```

#### 2. 文件上传
- 点击"上传日志"按钮
- 选择 AgentSight 日志文件
- 自动解析和可视化

#### 3. 文本粘贴
- 直接粘贴 JSON 事件日志
- 实时解析和验证
- 错误检测和纠正

### 导航

#### 时间线视图
- **缩放**：鼠标滚轮或缩放控件
- **平移**：点击拖拽时间线
- **过滤**：使用搜索栏和过滤控件
- **选择**：点击事件查看详情

#### 进程树
- **展开/折叠**：点击进程节点
- **过滤**：进程名、PID 或生命周期事件
- **详情**：悬停查看快速信息，点击查看完整详情

#### 控制面板
- **视图切换**：在时间线、进程树和日志视图之间切换
- **同步数据**：从 collector 手动刷新
- **清除数据**：重置所有加载的事件
- **导出**：下载过滤后的数据

## 配置

### 环境变量

```bash
# 数据同步的 API 端点
NEXT_PUBLIC_API_URL=http://localhost:7395

# 启用调试模式
NEXT_PUBLIC_DEBUG=true

# 自定义开发端口
PORT=3000
```

### 构建配置

查看 `next.config.js` 了解：
- 资源优化
- 构建输出配置
- 开发环境 vs 生产环境设置

## 开发

### 项目结构

```
agentsight/frontend/
├── src/
│   ├── app/           # Next.js app 目录
│   │   ├── page.tsx   # 主应用页面
│   │   └── layout.tsx # 应用布局
│   ├── components/    # React 组件
│   │   ├── LogView.tsx       # 日志检查视图
│   │   ├── TimelineView.tsx  # 交互式时间线
│   │   ├── ProcessTreeView.tsx # 进程层级
│   │   ├── UploadPanel.tsx   # 文件上传界面
│   │   ├── common/           # 共享组件
│   │   ├── log/              # 日志视图组件
│   │   ├── process-tree/     # 进程树组件
│   │   └── timeline/         # 时间线组件
│   ├── lib/           # 工具库
│   ├── types/         # TypeScript 类型定义
│   └── utils/         # 辅助函数
├── public/            # 静态资源
├── package.json       # 依赖和脚本
└── tailwind.config.ts # 样式配置
```

### 核心组件

#### EventFilters（`src/components/common/EventFilters.tsx`）
- 可配置的过滤界面
- 搜索、类型、来源和时间范围过滤
- 实时过滤应用

#### Timeline（`src/components/timeline/Timeline.tsx`）
- 核心时间线可视化
- 缩放、平移和选择处理
- 事件渲染和交互

#### ProcessNode（`src/components/process-tree/ProcessNode.tsx`）
- 单个进程可视化
- 生命周期状态管理
- 交互式展开和详情

### 开发命令

```bash
# 带热重载的开发服务器
npm run dev

# 类型检查
npm run type-check

# 代码检查和格式化
npm run lint
npm run lint:fix

# 构建和测试
npm run build
npm run start

# 清除构建缓存
rm -rf .next node_modules
npm install
```

### 添加新功能

#### 1. 新的可视化组件
```typescript
// src/components/MyView.tsx
import { Event } from '@/types/event';

interface MyViewProps {
  events: Event[];
}

export function MyView({ events }: MyViewProps) {
  // 组件实现
}
```

#### 2. 事件类型支持
```typescript
// src/types/event.ts
export interface MyEventData {
  // 新的事件数据结构
}

// src/utils/eventParsers.ts
export function parseMyEvent(data: any): MyEventData {
  // 解析逻辑
}
```

#### 3. 新的 Analyzer 集成
```typescript
// src/utils/eventProcessing.ts
export function processMyEvents(events: Event[]): ProcessedEvent[] {
  // 处理逻辑
}
```

## API 集成

### 数据端点

前端连接到 collector 的 REST API：

```typescript
// GET /api/events - 获取所有事件
// GET /api/events/stream - Server-Sent Events 流
// POST /api/events - 上传事件数据
```

### 事件格式

事件遵循标准化的 AgentSight 格式：

```typescript
interface Event {
  id: string;
  timestamp: number;
  source: string;
  pid: number;
  comm: string;
  data: Record<string, any>;
}
```

## 性能

### 优化特性

- **虚拟滚动**：高效处理大型事件数据集
- **懒加载**：按需加载组件和数据
- **记忆化**：防止不必要的重渲染
- **防抖过滤**：减少用户输入时的计算

### 内存管理

- **事件分页**：限制内存中的事件数量
- **数据清理**：自动清理旧事件
- **组件清理**：卸载时正确清理

## 部署

### Next.js 独立部署

```bash
# 构建独立应用
npm run build

# 将 dist/ 目录部署到 Web 服务器
# 需要 Node.js 运行时
```

### 嵌入到 Collector

```bash
# 构建前端用于嵌入
npm run build

# Collector 自动在 /timeline 提供服务
cd ../collector && cargo run server
```

### 容器部署

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

## 故障排除

### 常见问题

#### 1. 数据未加载
- 验证 collector 正在运行且可访问
- 检查浏览器控制台的网络错误
- 确保 CORS 配置正确

#### 2. 性能问题
- 使用过滤器减少事件数量
- 在浏览器开发工具中检查内存泄漏
- 对大数据集考虑分页

#### 3. 构建错误
- 清除 Next.js 缓存：`rm -rf .next`
- 更新依赖：`npm update`
- 检查 TypeScript 错误：`npm run type-check`

### 调试模式

```bash
# 启用调试日志
NEXT_PUBLIC_DEBUG=true npm run dev

# 检查浏览器控制台获取详细日志
# 网络标签页查看 API 通信
```

## 浏览器支持

- **Chrome**：90+（推荐）
- **Firefox**：88+
- **Safari**：14+
- **Edge**：90+

## 参与贡献

1. Fork 仓库
2. 创建功能分支：`git checkout -b feature/my-feature`
3. 遵循 TypeScript 和 React 最佳实践
4. 为新功能添加测试
5. 确保所有代码检查通过：`npm run lint`
6. 提交 Pull Request

### 代码规范

- **TypeScript**：严格模式，显式类型
- **组件**：函数式组件 + hooks
- **样式**：Tailwind CSS，一致的模式
- **测试**：Jest 和 React Testing Library

## 许可证

MIT 许可证 - 详见 [LICENSE](../LICENSE)。

## 相关项目

- **AgentSight Collector**：数据采集和分析（`../collector/`）
- **分析工具**：Python 数据处理工具（`../script/`）
- **文档**：综合指南和示例（`../docs/`）

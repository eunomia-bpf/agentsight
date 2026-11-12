# AgentSight Frontend

A modern, responsive web interface for the AgentSight AI agent observability platform. Built with Next.js, TypeScript, and Tailwind CSS.

## 🚀 Quick Start

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Open http://localhost:3000
```

## 📋 Documentation

- **[DESIGN.md](./DESIGN.md)** - Comprehensive technical design document
- **[USER_EXPERIENCE.md](./USER_EXPERIENCE.md)** - User journey and interaction patterns
- **[VISUALIZATION_EXAMPLES.md](./VISUALIZATION_EXAMPLES.md)** - UI mockups and examples
- **[FEATURES.md](./FEATURES.md)** - Key features and capabilities overview

## 🎯 Key Features

### **Zero-Instrumentation Monitoring**
- Monitor any AI agent framework without code changes
- System-level visibility via eBPF technology
- Independent monitoring at kernel level

### **Real-time Dashboards**
- Live agent status and performance metrics
- Interactive timelines with zoom and filtering
- Cross-agent coordination tracking
- Resource usage correlation with AI operations

### **Security & Compliance**
- Prompt injection detection and analysis
- Access control monitoring for files and network
- Policy compliance tracking and audit trails
- Real-time security event monitoring

### **Advanced Analytics**
- Response time analysis with percentile distributions
- Cost tracking across LLM providers and models
- Bottleneck identification and optimization suggestions
- Pattern recognition for similar issues

## 🏗️ Architecture

```
frontend/
├── src/
│   ├── app/                 # Next.js App Router pages
│   │   ├── dashboard/       # Main dashboard
│   │   ├── agents/          # Agent-specific views
│   │   ├── traces/          # Trace visualization
│   │   ├── security/        # Security monitoring
│   │   └── timeline/        # Timeline visualization
│   ├── components/          # Reusable UI components
│   │   ├── charts/          # Data visualization
│   │   ├── timeline/        # Timeline components
│   │   ├── filters/         # Search and filtering
│   │   └── ui/              # Base UI components
│   ├── lib/                 # Utilities and data fetching
│   │   ├── api/             # API client
│   │   ├── types/           # TypeScript definitions
│   │   └── utils/           # Helper functions
│   └── stores/              # State management
├── public/                  # Static assets
└── docs/                    # Additional documentation
```

## 🎨 Design System

### **Color Palette**
- **Primary**: Blue (#3B82F6) - Actions, links, brand
- **Secondary**: Purple (#8B5CF6) - Highlights, secondary actions
- **Success**: Green (#10B981) - Success states, positive metrics
- **Warning**: Orange (#F59E0B) - Warnings, attention needed
- **Error**: Red (#EF4444) - Errors, critical alerts

### **Component Types**
- **Metric Cards** - High-level KPI display
- **Event Timelines** - Chronological event visualization
- **Trace Trees** - Hierarchical trace exploration
- **Activity Feeds** - Real-time event streaming
- **Search Interfaces** - Advanced filtering and search

## 🔧 Technology Stack

- **Framework**: Next.js 14+ with App Router
- **Language**: TypeScript for type safety
- **Styling**: Tailwind CSS with custom design system
- **State Management**: Zustand for complex state, React Query for server state
- **Visualization**: D3.js, Recharts, custom WebGL components
- **Real-time**: Server-Sent Events (SSE) or WebSockets
- **Testing**: Jest, React Testing Library, Cypress

## 📱 Responsive Design

### **Desktop (1024px+)**
- Full-featured dashboard with multi-column layouts
- Advanced data visualization and interaction
- Complete feature set for power users

### **Tablet (768px-1024px)**
- Simplified two-column layouts
- Touch-friendly interactions
- Essential monitoring features

### **Mobile (320px-768px)**
- Single-column stack layout
- Priority-based information display
- Quick actions and alert management

## 🔐 Security Features

### **Data Protection**
- Configurable data masking for sensitive information
- Role-based access controls
- Secure session management
- Encrypted data transmission

### **Threat Detection**
- Real-time prompt injection detection
- Unauthorized access monitoring
- Policy violation tracking
- Security incident response tools

## 🚀 Performance

### **Optimization Techniques**
- Virtual scrolling for large datasets
- Efficient real-time updates via WebSockets/SSE
- Intelligent caching and data management
- Code splitting and lazy loading

### **Metrics**
- **Load Time**: < 2 seconds for initial dashboard
- **Real-time Latency**: < 100ms for live updates
- **Memory Usage**: Optimized for long-running sessions
- **Mobile Performance**: 60fps animations on mobile devices

## 🌐 Accessibility

### **WCAG 2.1 AA Compliance**
- Keyboard navigation support
- Screen reader compatibility
- High contrast mode
- Color-blind friendly design

### **Keyboard Shortcuts**
- `Alt + 1-5`: Navigate between main sections
- `/`: Focus global search
- `Escape`: Close modals and dropdowns
- `Tab`: Navigate interactive elements

## 🔌 API Integration

### **Real-time Data Streams**
```typescript
GET /api/v1/stream/events        // Server-sent events
GET /api/v1/stream/traces        // Real-time trace updates
GET /api/v1/stream/alerts        // Security and performance alerts
```

### **Historical Data Queries**
```typescript
GET /api/v1/traces               // Query historical traces
GET /api/v1/agents               // Agent information and status
GET /api/v1/conversations        // Conversation history
GET /api/v1/security/events      // Security events and alerts
```

## 🧪 Testing

### **Unit Tests**
```bash
npm run test              # Run Jest unit tests
npm run test:watch        # Run tests in watch mode
npm run test:coverage     # Generate coverage report
```

### **Integration Tests**
```bash
npm run test:integration  # Run integration tests
npm run test:e2e          # Run Playwright end-to-end tests
```

### **Performance Tests**
```bash
npm run test:performance  # Run performance benchmarks
npm run lighthouse        # Run Lighthouse audits
```

## 🚢 Deployment

### **Production Build**
```bash
npm run build             # Build for production
npm run start             # Start production server
```

### **Environment Variables**
```env
NEXT_PUBLIC_API_URL=http://localhost:7395
NEXT_PUBLIC_WEBSOCKET_URL=ws://localhost:7395/ws
NEXT_PUBLIC_ENVIRONMENT=production
```

### **Docker Deployment**
```dockerfile
# Build stage
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Production stage
FROM node:18-alpine AS runner
WORKDIR /app
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
EXPOSE 3000
CMD ["node", "server.js"]
```

## 📈 Monitoring

### **Application Metrics**
- Error tracking with Sentry
- Performance monitoring with Web Vitals
- User analytics with privacy-first approach
- Real-time application health checks

### **User Experience Metrics**
- Time to first insight
- Task completion rates
- Feature adoption tracking
- User satisfaction scores

## 🤝 Contributing

### **Development Setup**
1. Clone the repository
2. Install dependencies: `npm install`
3. Start development server: `npm run dev`
4. Make your changes
5. Run tests: `npm run test`
6. Submit a pull request

### **Code Style**
- ESLint and Prettier configuration included
- TypeScript strict mode enabled
- Conventional commit messages
- Component-first development approach

## 🔄 Roadmap

### **Phase 1** (Current)
- [x] Basic dashboard layout
- [x] Timeline visualization
- [ ] Agent monitoring interface
- [ ] Basic search and filtering

### **Phase 2** (Next 3 months)
- [ ] Advanced trace visualization
- [ ] Security dashboard
- [ ] Performance analytics
- [ ] Mobile optimization

### **Phase 3** (Next 6 months)
- [ ] AI-powered insights
- [ ] Advanced integrations
- [ ] Multi-tenant support
- [ ] Enterprise features

## 📞 Support

- **Documentation**: See the docs/ folder for detailed guides
- **Issues**: Report bugs and feature requests via GitHub Issues
- **Community**: Join our Discord server for discussions
- **Enterprise**: Contact us for enterprise support and custom features

---

**AgentSight Frontend** - The modern interface for comprehensive AI agent observability. Built for developers, security teams, and operations engineers who need deep visibility into their AI systems.

## 🔗 Related Projects

- **[AgentSight Collector](../collector/)** - eBPF-based data collection backend
- **[AgentSight Docs](../docs/)** - Comprehensive documentation
- **[AgentSight Examples](../examples/)** - Usage examples and tutorials

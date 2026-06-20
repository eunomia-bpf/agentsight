# Artifact Examples

## Example 1: Session Cost Analysis

### Input

AgentSight record DB with 3 sessions over 2 hours.

### Generated Finding

```html
<div class="finding finding-high">
  <h3>
    <span class="severity-badge severity-high">HIGH</span>
    Token Waste: Retry Storm in Session claude-abc123
  </h3>
  <p>
    Session spent <strong>45,000 tokens</strong> ($1.35) on 3 failed edit attempts
    before succeeding on the 4th try.
  </p>
  <p>
    <strong>Evidence:</strong> Calls at 14:23:01, 14:23:15, 14:23:28 all targeted 
    <code>src/main.rs</code> with syntax errors.
  </p>
  <p>
    <strong>Recommendation:</strong> Add syntax validation before edit completion
    to fail fast on malformed changes.
  </p>
</div>
```

### Generated Metrics Grid

```html
<div class="metrics-grid">
  <div class="metric-card">
    <div class="metric-value">3</div>
    <div class="metric-label">Sessions</div>
  </div>
  <div class="metric-card">
    <div class="metric-value">890K</div>
    <div class="metric-label">Total Tokens</div>
  </div>
  <div class="metric-card">
    <div class="metric-value">$4.23</div>
    <div class="metric-label">Estimated Cost</div>
  </div>
  <div class="metric-card">
    <div class="metric-value">72%</div>
    <div class="metric-label">Tool Success Rate</div>
  </div>
</div>
```

## Example 2: Public Aggregate Report

### Input

AgentSight monitor DB covering 1 week.

### Generated Summary (Public Mode)

```html
<section class="executive-summary">
  <h2>Summary</h2>
  <ul>
    <li><strong>47 sessions</strong> across 12 projects over 7 days</li>
    <li><strong>Claude Code</strong> accounted for 68% of sessions</li>
    <li><strong>3 sessions</strong> exceeded $5 estimated cost</li>
    <li><strong>Cache efficiency</strong> averaged 45% (below 60% target)</li>
  </ul>
  
  <h3>Recommendation</h3>
  <p>
    Improve prompt caching by stabilizing system prompts. Top 3 expensive sessions
    had < 20% cache hit rate.
  </p>
</section>
```

Note: No session IDs, file paths, or prompt content included in public mode.

## Example 3: Model Distribution Table

```html
<h3>Token Usage by Model</h3>
<table class="evidence-table">
  <thead>
    <tr>
      <th data-sortable="text">Model</th>
      <th data-sortable="number">Calls</th>
      <th data-sortable="number">Input Tokens</th>
      <th data-sortable="number">Output Tokens</th>
      <th data-sortable="number">Est. Cost</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>claude-sonnet-4</td>
      <td>156</td>
      <td>1,234,567</td>
      <td>234,567</td>
      <td>$7.23</td>
    </tr>
    <tr>
      <td>claude-haiku-3.5</td>
      <td>89</td>
      <td>456,789</td>
      <td>78,901</td>
      <td>$0.68</td>
    </tr>
    <tr>
      <td>claude-opus-4</td>
      <td>12</td>
      <td>123,456</td>
      <td>45,678</td>
      <td>$5.27</td>
    </tr>
  </tbody>
</table>
```

## Example 4: Timeline Events

```html
<section class="timeline collapsible">
  <h2>Event Timeline</h2>
  <div class="timeline-events">
    <div class="timeline-event">
      <span class="timeline-time">14:23:01</span>
      <div class="timeline-content">
        <strong>LLM Call</strong>: claude-sonnet-4, 15K tokens
      </div>
    </div>
    <div class="timeline-event">
      <span class="timeline-time">14:23:08</span>
      <div class="timeline-content">
        <strong>Tool: edit</strong>: src/main.rs 
        <span class="status-failed">FAILED</span>
      </div>
    </div>
    <div class="timeline-event">
      <span class="timeline-time">14:23:15</span>
      <div class="timeline-content">
        <strong>LLM Call</strong>: claude-sonnet-4, 15K tokens (retry)
      </div>
    </div>
  </div>
</section>
```

## Example 5: Evidence Gaps Section

```html
<section class="evidence-gaps">
  <h3>Evidence Gaps</h3>
  <ul>
    <li>
      <strong>Missing:</strong> Raw prompts (privacy setting: public)
    </li>
    <li>
      <strong>Limited:</strong> Resource samples only available for 2 of 3 sessions
    </li>
    <li>
      <strong>Aggregate only:</strong> Monitor DB does not include per-call token counts
    </li>
  </ul>
  
  <h4>For deeper analysis:</h4>
  <ol>
    <li>Run <code>agentsight report export --include-prompts</code> for full detail</li>
    <li>Enable resource monitoring for all sessions</li>
    <li>Use record mode instead of monitor for production sessions</li>
  </ol>
</section>
```

## Full Artifact Example (Condensed)

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Agent Behavior Report - 2026-06-19</title>
  <style>/* CSS here */</style>
</head>
<body>
  <header class="artifact-header">
    <h1>Agent Behavior Report</h1>
    <div class="metadata">
      <span>Generated: 2026-06-19 15:30:00</span>
      <span>Source: agentsight-20260619-120000.db</span>
      <span class="privacy-badge internal">Internal</span>
    </div>
  </header>

  <main>
    <section class="executive-summary">
      <div class="metrics-grid"><!-- 4 metric cards --></div>
      <h3>Key Findings</h3>
      <ul>
        <li>1 HIGH: Retry storm cost $1.35 in wasted tokens</li>
        <li>2 MEDIUM: Cache efficiency below target</li>
        <li>1 LOW: Unused tool calls detected</li>
      </ul>
    </section>

    <section class="findings">
      <h2>Findings</h2>
      <!-- 4 finding cards -->
    </section>

    <section class="evidence">
      <h2>Evidence</h2>
      <!-- Session table -->
      <!-- Model distribution table -->
      <!-- Tool success rate table -->
    </section>

    <section class="timeline collapsible">
      <h2>Timeline</h2>
      <!-- 47 timeline events -->
    </section>
  </main>

  <script>/* JS here */</script>
</body>
</html>
```

# HTML Template Reference

## Base Template Structure

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Agent Behavior Report - {{date}}</title>
  <style>
    /* Embedded CSS - see below */
  </style>
</head>
<body>
  <header class="artifact-header">
    <h1>Agent Behavior Report</h1>
    <div class="metadata">
      <span class="date">Generated: {{timestamp}}</span>
      <span class="source">Source: {{data_source}}</span>
      <span class="privacy-badge {{privacy_level}}">{{privacy_level}}</span>
    </div>
  </header>

  <main>
    <section class="executive-summary">
      <h2>Summary</h2>
      <!-- Key findings and metrics -->
    </section>

    <section class="findings">
      <h2>Findings</h2>
      <!-- Individual finding cards -->
    </section>

    <section class="evidence">
      <h2>Evidence</h2>
      <!-- Data tables -->
    </section>

    <section class="timeline collapsible">
      <h2>Timeline</h2>
      <!-- Event timeline -->
    </section>
  </main>

  <script>
    /* Embedded JavaScript - see below */
  </script>
</body>
</html>
```

## CSS Styles

```css
:root {
  --color-bg: #ffffff;
  --color-text: #1a1a1a;
  --color-border: #e5e5e5;
  --color-high: #dc2626;
  --color-medium: #f59e0b;
  --color-low: #22c55e;
  --color-info: #3b82f6;
}

@media (prefers-color-scheme: dark) {
  :root {
    --color-bg: #1a1a1a;
    --color-text: #f5f5f5;
    --color-border: #333333;
  }
}

* {
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  line-height: 1.6;
  color: var(--color-text);
  background: var(--color-bg);
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

.artifact-header {
  border-bottom: 2px solid var(--color-border);
  padding-bottom: 1rem;
  margin-bottom: 2rem;
}

.artifact-header h1 {
  margin: 0 0 0.5rem 0;
}

.metadata {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
  font-size: 0.875rem;
  color: #666;
}

.privacy-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}

.privacy-badge.internal {
  background: #dbeafe;
  color: #1e40af;
}

.privacy-badge.public {
  background: #dcfce7;
  color: #166534;
}

/* Finding cards */
.finding {
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1rem;
  border-left: 4px solid var(--color-info);
}

.finding-high {
  border-left-color: var(--color-high);
}

.finding-medium {
  border-left-color: var(--color-medium);
}

.finding-low {
  border-left-color: var(--color-low);
}

.finding h3 {
  margin: 0 0 0.5rem 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.severity-badge {
  padding: 0.125rem 0.375rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}

.severity-high {
  background: #fee2e2;
  color: var(--color-high);
}

.severity-medium {
  background: #fef3c7;
  color: #b45309;
}

.severity-low {
  background: #dcfce7;
  color: #166534;
}

/* Metric cards */
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.metric-card {
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 1rem;
  text-align: center;
}

.metric-value {
  font-size: 2rem;
  font-weight: 700;
  color: var(--color-info);
}

.metric-label {
  font-size: 0.875rem;
  color: #666;
}

/* Tables */
.evidence-table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 1rem;
}

.evidence-table th,
.evidence-table td {
  padding: 0.75rem;
  text-align: left;
  border-bottom: 1px solid var(--color-border);
}

.evidence-table th {
  background: #f5f5f5;
  font-weight: 600;
}

.evidence-table tr:hover {
  background: #f9f9f9;
}

/* Collapsible sections */
.collapsible > h2 {
  cursor: pointer;
  user-select: none;
}

.collapsible > h2::before {
  content: '▶ ';
  font-size: 0.75rem;
}

.collapsible.open > h2::before {
  content: '▼ ';
}

.collapsible > *:not(h2) {
  display: none;
}

.collapsible.open > * {
  display: block;
}

/* Timeline */
.timeline-event {
  display: flex;
  gap: 1rem;
  padding: 0.5rem 0;
  border-left: 2px solid var(--color-border);
  padding-left: 1rem;
  margin-left: 0.5rem;
}

.timeline-time {
  font-size: 0.75rem;
  color: #666;
  min-width: 100px;
}

.timeline-content {
  flex: 1;
}

/* Print styles */
@media print {
  body {
    padding: 0;
    font-size: 12pt;
  }
  
  .collapsible > * {
    display: block !important;
  }
  
  .no-print {
    display: none;
  }
}
```

## JavaScript

```javascript
// Collapsible sections
document.querySelectorAll('.collapsible > h2').forEach(header => {
  header.addEventListener('click', () => {
    header.parentElement.classList.toggle('open');
  });
});

// Table sorting
document.querySelectorAll('.evidence-table th[data-sortable]').forEach(th => {
  th.style.cursor = 'pointer';
  th.addEventListener('click', () => {
    const table = th.closest('table');
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    const col = th.cellIndex;
    const isNumeric = th.dataset.sortable === 'number';
    const isAsc = th.dataset.sortDir !== 'asc';
    
    rows.sort((a, b) => {
      const aVal = a.cells[col].textContent;
      const bVal = b.cells[col].textContent;
      if (isNumeric) {
        return isAsc 
          ? parseFloat(aVal) - parseFloat(bVal)
          : parseFloat(bVal) - parseFloat(aVal);
      }
      return isAsc
        ? aVal.localeCompare(bVal)
        : bVal.localeCompare(aVal);
    });
    
    th.dataset.sortDir = isAsc ? 'asc' : 'desc';
    rows.forEach(row => tbody.appendChild(row));
  });
});

// Copy to clipboard
document.querySelectorAll('.copy-button').forEach(btn => {
  btn.addEventListener('click', () => {
    const target = document.getElementById(btn.dataset.target);
    navigator.clipboard.writeText(target.textContent);
    btn.textContent = 'Copied!';
    setTimeout(() => btn.textContent = 'Copy', 2000);
  });
});
```

## Data Binding

Use these placeholders in the template:

| Placeholder | Description |
|-------------|-------------|
| `{{timestamp}}` | Generation timestamp |
| `{{data_source}}` | Source description |
| `{{privacy_level}}` | internal or public |
| `{{date_range}}` | Start to end date |
| `{{session_count}}` | Total sessions |
| `{{total_tokens}}` | Total token count |
| `{{estimated_cost}}` | Cost in USD |
| `{{findings}}` | Rendered finding cards |
| `{{session_table}}` | Session summary table |
| `{{model_table}}` | Model distribution table |
| `{{timeline_events}}` | Timeline event list |

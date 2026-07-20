#!/usr/bin/env python3
"""Build a task-centric semantic flamegraph from a real AgentReward trace.

This is a visualization-shape prototype, not an automatic task-induction
accuracy result.  It deliberately starts from one concrete benchmark task and
uses a small, declared phase-to-subtask map so the stack answers a user-facing
question:

    task -> subtask -> phase -> semantic action -> observed outcome

The source operation count and token widths are read from the tracked R300
operation file.  Agent/model identity remains a filter in the interactive HTML
rather than consuming a stack level.
"""

from __future__ import annotations

import argparse
import html
import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "docs/visexp/out/operation-query-utility-r300/query-utility-operations.jsonl"
DEFAULT_OUTPUT = ROOT / "docs/visexp/out/task-centric-flamegraph-prototype"
SESSION = "workarena.servicenow.infeasible-navigate-and-order-loaner-laptop-with-reason-l2"
TASK_LABEL = "Order a loaner laptop and provide a reason"

PHASE_TO_SUBTASK = {
    "observe": "Understand the request",
    "navigate": "Locate catalog and item",
    "input": "Configure the request",
    "browser-action": "Configure the request",
    "finish": "Complete or report",
}

PHASE_LABELS = {
    "observe": "Observe",
    "navigate": "Navigate",
    "input": "Enter details",
    "browser-action": "Choose options",
    "finish": "Finish",
}

ACTION_LABELS = {
    "noop": "Inspect page",
    "click": "Click",
    "fill": "Fill field",
    "select_option": "Select option",
    "send_msg_to_user": "Send final response",
    "report_infeasible": "Report infeasible",
}

FRAME_COLORS = {
    "Task": "#23395d",
    "Subtask:Understand the request": "#6c5ce7",
    "Subtask:Locate catalog and item": "#2f80ed",
    "Subtask:Configure the request": "#00a6a6",
    "Subtask:Complete or report": "#8e5bd9",
    "Phase": "#72a7e8",
    "Action": "#a8c7ee",
    "Outcome:Progress": "#43b581",
    "Outcome:Repeated": "#f3a712",
    "Outcome:Repeated 3+ times": "#ef7c2f",
    "Outcome:Action error": "#d64550",
}


@dataclass(frozen=True)
class Sample:
    stack: tuple[str, ...]
    operations: int
    tokens: int
    agent: str
    repeat: bool
    task_failed: bool


@dataclass
class Node:
    frame: str
    operations: int = 0
    tokens: int = 0
    children: dict[str, "Node"] = field(default_factory=dict)


def frame(kind: str, label: str) -> str:
    return f"{kind} · {label}"


def frame_parts(value: str) -> tuple[str, str]:
    parts = value.split(" · ", 1)
    return (parts[0], parts[1]) if len(parts) == 2 else ("", value)


def outcome_for(fields: dict[str, Any]) -> str:
    if str(fields.get("step_error", "ok")) != "ok":
        return "Action error"
    repeat_state = str(fields.get("repeat_state", "single"))
    if repeat_state == "same-action-run":
        return "Repeated 3+ times"
    if repeat_state == "light-repeat":
        return "Repeated"
    return "Progress"


def short_agent(value: str) -> str:
    lowered = value.lower()
    if "claude" in lowered:
        return "Claude 3.7 Sonnet"
    if "gpt-4o" in lowered:
        return "GPT-4o"
    if "llama" in lowered:
        return "Llama 3.3 70B"
    if "qwen" in lowered:
        return "Qwen2.5-VL 72B"
    return value.replace("genericagent-", "")


def read_samples(source: Path) -> list[Sample]:
    samples: list[Sample] = []
    with source.open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            fields = record.get("fields", {})
            if fields.get("session") != SESSION:
                continue

            phase_raw = str(fields.get("phase", "unknown"))
            action_raw = str(fields.get("action", "unknown"))
            subtask = PHASE_TO_SUBTASK.get(phase_raw, "Other work")
            phase_label = PHASE_LABELS.get(phase_raw, phase_raw.replace("-", " ").title())
            action_label = ACTION_LABELS.get(action_raw, action_raw.replace("_", " ").title())
            outcome = outcome_for(fields)
            try:
                tokens = int(fields.get("input_tokens", 0)) + int(fields.get("output_tokens", 0))
            except (TypeError, ValueError):
                tokens = 0
            samples.append(
                Sample(
                    stack=(
                        frame("Task", TASK_LABEL),
                        frame("Subtask", subtask),
                        frame("Phase", phase_label),
                        frame("Action", action_label),
                        frame("Outcome", outcome),
                    ),
                    operations=max(1, int(record.get("value", 1))),
                    tokens=max(0, tokens),
                    agent=short_agent(str(fields.get("agent", "unknown"))),
                    repeat=outcome.startswith("Repeated"),
                    task_failed=str(fields.get("status", "")).lower() == "failure",
                )
            )
    if not samples:
        raise RuntimeError(f"no operations found for session {SESSION!r} in {source}")
    return samples


def build_tree(samples: Iterable[Sample]) -> Node:
    root = Node("root")
    for sample in samples:
        root.operations += sample.operations
        root.tokens += sample.tokens
        node = root
        for item in sample.stack:
            node = node.children.setdefault(item, Node(item))
            node.operations += sample.operations
            node.tokens += sample.tokens
    return root


def node_value(node: Node, metric: str) -> int:
    return node.operations if metric == "operations" else node.tokens


def sorted_children(node: Node, metric: str) -> list[Node]:
    return sorted(node.children.values(), key=lambda child: (-node_value(child, metric), child.frame))


def color_for(value: str) -> str:
    kind, label = frame_parts(value)
    if kind == "Task":
        return FRAME_COLORS["Task"]
    if kind == "Subtask":
        return FRAME_COLORS.get(f"Subtask:{label}", "#5b7c99")
    if kind == "Phase":
        return FRAME_COLORS["Phase"]
    if kind == "Action":
        return FRAME_COLORS["Action"]
    if kind == "Outcome":
        return FRAME_COLORS.get(f"Outcome:{label}", "#7f8c8d")
    return "#7f8c8d"


def text_color(value: str) -> str:
    kind, _ = frame_parts(value)
    return "#10233f" if kind == "Action" else "#ffffff"


def compact_number(value: int, metric: str) -> str:
    if metric == "operations":
        return f"{value:,} ops"
    if value >= 1_000_000:
        return f"{value / 1_000_000:.2f}M tok"
    if value >= 1_000:
        return f"{value / 1_000:.1f}K tok"
    return f"{value:,} tok"


def truncate(text: str, width: float) -> str:
    max_chars = max(0, int((width - 14) / 7.0))
    if max_chars < 4:
        return ""
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1] + "…"


def write_static_svg(path: Path, samples: list[Sample], metric: str) -> None:
    tree = build_tree(samples)
    total = max(1, node_value(tree, metric))
    width = 1600
    plot_x = 154
    plot_width = width - plot_x - 28
    top = 126
    frame_height = 42
    max_depth = 5
    height = top + max_depth * frame_height + 38
    unit_label = "observed operations" if metric == "operations" else "reported input + output tokens"

    chunks = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<style>",
        "text{font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif}",
        ".title{font-size:22px;font-weight:750;fill:#17253d}",
        ".subtitle{font-size:12px;fill:#60708a}",
        ".layer{font-size:11px;font-weight:700;fill:#738096;text-transform:uppercase;letter-spacing:.08em}",
        ".frame rect{stroke:#fff;stroke-width:2}",
        ".frame:hover rect{stroke:#17253d;stroke-width:2.5}",
        ".label{font-size:12px;font-weight:700}",
        ".value{font-size:10px;font-weight:500;opacity:.9}",
        ".legend{font-size:11px;fill:#44516a}",
        "</style>",
        '<rect width="100%" height="100%" fill="#f7f9fc"/>',
        '<text class="title" x="28" y="34">Task-centric semantic flamegraph</text>',
        f'<text class="subtitle" x="28" y="57">Concrete task → subtask → phase → semantic action → observed outcome · width = {html.escape(unit_label)}</text>',
        f'<text class="subtitle" x="28" y="78">{len(samples)} trace rows · {len(set(sample.agent for sample in samples))} agent attempts · hover a frame for its full task path</text>',
    ]

    legend = [
        ("Progress", FRAME_COLORS["Outcome:Progress"]),
        ("Repeated", FRAME_COLORS["Outcome:Repeated"]),
        ("Repeated 3+ times", FRAME_COLORS["Outcome:Repeated 3+ times"]),
        ("Action error", FRAME_COLORS["Outcome:Action error"]),
    ]
    legend_x = 930
    for label, fill in legend:
        chunks.append(f'<rect x="{legend_x}" y="68" width="12" height="12" rx="3" fill="{fill}"/>')
        chunks.append(f'<text class="legend" x="{legend_x + 18}" y="78">{html.escape(label)}</text>')
        legend_x += 26 + len(label) * 7

    layers = ["Outcome", "Action", "Phase", "Subtask", "Task"]
    for index, label in enumerate(layers):
        y = top + index * frame_height + 25
        chunks.append(f'<text class="layer" x="28" y="{y}">{label}</text>')

    def render(node: Node, x: float, depth: int, prefix: tuple[str, ...]) -> None:
        value = node_value(node, metric)
        rect_width = value / total * plot_width
        if rect_width < 0.7:
            return
        y = top + (max_depth - depth) * frame_height
        _, label = frame_parts(node.frame)
        pct = 100 * value / total
        path_text = " → ".join(frame_parts(item)[1] for item in prefix + (node.frame,))
        tooltip = html.escape(f"{path_text}\n{compact_number(value, metric)} ({pct:.1f}% of task)")
        label_text = truncate(label, rect_width)
        chunks.append(f'<g class="frame"><title>{tooltip}</title>')
        chunks.append(
            f'<rect x="{x:.3f}" y="{y}" width="{rect_width:.3f}" height="{frame_height - 3}" rx="6" fill="{color_for(node.frame)}"/>'
        )
        if label_text:
            chunks.append(
                f'<text class="label" x="{x + 8:.3f}" y="{y + 16}" fill="{text_color(node.frame)}">{html.escape(label_text)}</text>'
            )
            value_text = compact_number(value, metric)
            if rect_width > len(value_text) * 6.2 + 16:
                chunks.append(
                    f'<text class="value" x="{x + 8:.3f}" y="{y + 31}" fill="{text_color(node.frame)}">{html.escape(value_text)} · {pct:.1f}%</text>'
                )
        chunks.append("</g>")
        child_x = x
        for child in sorted_children(node, metric):
            render(child, child_x, depth + 1, prefix + (node.frame,))
            child_x += node_value(child, metric) / total * plot_width

    child_x = float(plot_x)
    for child in sorted_children(tree, metric):
        render(child, child_x, 1, ())
        child_x += node_value(child, metric) / total * plot_width

    chunks.append("</svg>")
    path.write_text("\n".join(chunks) + "\n", encoding="utf-8")


def sample_payload(samples: list[Sample]) -> list[dict[str, Any]]:
    return [
        {
            "stack": list(sample.stack),
            "operations": sample.operations,
            "tokens": sample.tokens,
            "agent": sample.agent,
            "repeat": sample.repeat,
            "taskFailed": sample.task_failed,
        }
        for sample in samples
    ]


def write_interactive_html(path: Path, samples: list[Sample]) -> None:
    payload = json.dumps(sample_payload(samples), ensure_ascii=False, separators=(",", ":"))
    agents = sorted(set(sample.agent for sample in samples))
    options = "".join(f'<option value="{html.escape(agent)}">{html.escape(agent)}</option>' for agent in agents)
    document = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Task-centric semantic flamegraph</title>
<style>
:root{--ink:#17253d;--muted:#66758d;--line:#dde4ef;--panel:#fff;--bg:#f3f6fb;--accent:#315efb}
*{box-sizing:border-box} body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.45 Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
.shell{max-width:1500px;margin:0 auto;padding:28px}.header{display:flex;justify-content:space-between;gap:24px;align-items:flex-start;margin-bottom:18px}
.eyebrow{color:#315efb;font-size:12px;font-weight:800;letter-spacing:.11em;text-transform:uppercase}.header h1{font-size:28px;line-height:1.15;margin:6px 0 8px}.subtitle{color:var(--muted);max-width:860px}
.badge{white-space:nowrap;background:#e9efff;color:#2749bd;border:1px solid #cad7ff;padding:8px 11px;border-radius:999px;font-size:12px;font-weight:700}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:18px;box-shadow:0 12px 36px rgba(38,55,85,.08)}
.controls{display:flex;align-items:center;gap:12px;flex-wrap:wrap;padding:15px 18px;border-bottom:1px solid var(--line)}
.segmented{display:inline-flex;background:#edf1f7;padding:3px;border-radius:10px}.segmented button{border:0;background:transparent;color:#59677d;border-radius:8px;padding:8px 12px;font-weight:700;cursor:pointer}.segmented button.active{background:#fff;color:var(--ink);box-shadow:0 1px 4px rgba(27,42,68,.16)}
label{font-size:12px;color:var(--muted);font-weight:700} select,input[type=search]{border:1px solid #ccd6e4;border-radius:9px;background:#fff;color:var(--ink);padding:8px 10px;outline:none}select:focus,input:focus{border-color:#6f8df7;box-shadow:0 0 0 3px #e7edff}
.check{display:flex;align-items:center;gap:7px;padding:0 4px}.check input{accent-color:var(--accent)}.spacer{flex:1}.reset{border:1px solid #cfd8e6;background:#fff;color:#3f4d64;border-radius:9px;padding:8px 11px;font-weight:700;cursor:pointer}.reset:disabled{opacity:.4;cursor:default}
.stats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;padding:16px 18px 0}.stat{background:#f7f9fc;border:1px solid #e2e8f1;border-radius:12px;padding:12px 14px}.stat strong{display:block;font-size:21px}.stat span{font-size:11px;color:var(--muted);font-weight:700;text-transform:uppercase;letter-spacing:.06em}
.breadcrumbs{padding:14px 18px 0;color:#66758d;font-size:12px;min-height:33px}.breadcrumbs b{color:#2b3b55}.chart-wrap{padding:4px 16px 18px}.chart-wrap svg{display:block;width:100%;height:auto;min-height:270px}.frame{cursor:pointer}.frame rect{stroke:#fff;stroke-width:2;transition:opacity .15s,stroke .15s}.frame:hover rect{stroke:#17253d;stroke-width:2.5}.frame.dim{opacity:.18}.layer{font-size:11px;font-weight:800;fill:#75829a;letter-spacing:.08em;text-transform:uppercase}.frame-label{font-size:12px;font-weight:750}.frame-value{font-size:10px;font-weight:550;opacity:.9}
.legend{display:flex;gap:14px;flex-wrap:wrap;padding:0 20px 18px;color:#59677d;font-size:12px}.legend span{display:flex;align-items:center;gap:6px}.swatch{width:10px;height:10px;border-radius:3px}
.insights{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-top:16px}.insight{padding:16px 17px}.insight h3{font-size:14px;margin:0 0 5px}.insight p{color:var(--muted);margin:0;font-size:13px}.insight strong{color:var(--ink)}
.provenance{margin-top:16px;padding:15px 18px;color:#60708a;font-size:12px}.provenance code{color:#35445d}
.tip{position:fixed;z-index:20;pointer-events:none;display:none;max-width:440px;background:#13213a;color:#fff;padding:10px 12px;border-radius:10px;box-shadow:0 10px 30px rgba(0,0,0,.25);font-size:12px}.tip b{display:block;margin-bottom:4px}.tip .muted{color:#bdc9da}
@media(max-width:850px){.stats,.insights{grid-template-columns:1fr 1fr}.header{display:block}.badge{display:inline-block;margin-top:12px}}@media(max-width:560px){.stats,.insights{grid-template-columns:1fr}.shell{padding:14px}}
</style>
</head>
<body>
<main class="shell">
  <div class="header">
    <div><div class="eyebrow">AgentProf · task view prototype</div><h1>Order a loaner laptop and provide a reason</h1><div class="subtitle">The stack follows the user's concrete task, then narrows through subtask, phase, semantic action, and observed outcome. Agent and model are filters, not stack frames.</div></div>
    <div class="badge">Real AgentReward trace · 4 attempts</div>
  </div>
  <section class="panel">
    <div class="controls">
      <div class="segmented"><button class="metric active" data-metric="operations">Operations</button><button class="metric" data-metric="tokens">Tokens</button></div>
      <label for="agent">Attempt</label><select id="agent"><option value="all">All agents</option>__OPTIONS__</select>
      <label class="check"><input id="issues" type="checkbox">Only repeated/error paths</label>
      <div class="spacer"></div><input id="search" type="search" placeholder="Search frames…"><button id="reset" class="reset" disabled>Reset zoom</button>
    </div>
    <div class="stats"><div class="stat"><strong id="ops">–</strong><span>operations</span></div><div class="stat"><strong id="tokens">–</strong><span>input + output tokens</span></div><div class="stat"><strong id="attempts">–</strong><span>visible attempts</span></div><div class="stat"><strong id="repeats">–</strong><span>repeat share</span></div></div>
    <div id="breadcrumbs" class="breadcrumbs"><b>Zoom:</b> full task</div>
    <div class="chart-wrap"><svg id="chart" viewBox="0 0 1600 270" role="img" aria-label="Task-centric semantic flamegraph"></svg></div>
    <div class="legend"><span><i class="swatch" style="background:#43b581"></i>Progress</span><span><i class="swatch" style="background:#f3a712"></i>Repeated</span><span><i class="swatch" style="background:#ef7c2f"></i>Repeated 3+ times</span><span><i class="swatch" style="background:#d64550"></i>Action error</span><span>Width is the selected metric; click any frame to zoom.</span></div>
  </section>
  <section class="insights">
    <article class="panel insight"><h3>The task failed without many low-level errors</h3><p>All four recorded attempts failed, but only <strong>2 of 204</strong> operations report an action error. The flame shape points to strategy/repetition, not merely tool breakage.</p></article>
    <article class="panel insight"><h3>Repetition clusters late in the task</h3><p><strong>20 of 26</strong> finish operations and <strong>14 of 30</strong> input operations are repeated, compared with 20 of 120 navigation operations.</p></article>
    <article class="panel insight"><h3>Task semantics stay primary</h3><p>Model identity is available through the attempt filter. It does not displace task, subtask, phase, action, or outcome from the causal reading path.</p></article>
  </section>
  <section class="panel provenance"><strong>Construction:</strong> session identifies the concrete task; a declared phase→subtask map supplies readable task decomposition; phase, action, repeat state, step error, and tokens come from the trace. No oracle/diagnostic label is used to build the stack. This artifact demonstrates the visualization shape, not automatic semantic-induction accuracy.<br><code>source: docs/visexp/out/operation-query-utility-r300/query-utility-operations.jsonl</code></section>
</main>
<div id="tip" class="tip"></div>
<script>
const samples=__SAMPLES__;
const colors={"Task":"#23395d","Subtask:Understand the request":"#6c5ce7","Subtask:Locate catalog and item":"#2f80ed","Subtask:Configure the request":"#00a6a6","Subtask:Complete or report":"#8e5bd9","Phase":"#72a7e8","Action":"#a8c7ee","Outcome:Progress":"#43b581","Outcome:Repeated":"#f3a712","Outcome:Repeated 3+ times":"#ef7c2f","Outcome:Action error":"#d64550"};
let metric="operations",zoomPath=[];
const $=id=>document.getElementById(id),svg=$("chart"),tip=$("tip");
const parts=s=>{const p=s.split(" · ");return [p.shift(),p.join(" · ")]};
const color=s=>{const [k,l]=parts(s);return colors[k+":"+l]||colors[k]||"#7f8c8d"};
const textColor=s=>parts(s)[0]==="Action"?"#10233f":"#fff";
const fmt=(v,m)=>m==="operations"?v.toLocaleString()+" ops":v>=1e6?(v/1e6).toFixed(2)+"M tok":v>=1e3?(v/1e3).toFixed(1)+"K tok":v.toLocaleString()+" tok";
function visibleSamples(){const a=$("agent").value,issues=$("issues").checked;return samples.filter(s=>(a==="all"||s.agent===a)&&(!issues||s.repeat||s.stack.at(-1).includes("Action error")));}
function tree(rows){const root={frame:"root",operations:0,tokens:0,children:new Map(),path:[]};for(const s of rows){root.operations+=s.operations;root.tokens+=s.tokens;let n=root;for(const f of s.stack){if(!n.children.has(f))n.children.set(f,{frame:f,operations:0,tokens:0,children:new Map(),path:[...n.path,f]});n=n.children.get(f);n.operations+=s.operations;n.tokens+=s.tokens;}}return root;}
function locate(root,path){let n=root;for(const f of path){n=n.children.get(f);if(!n)return root;}return n;}
function el(name,attrs={}){const n=document.createElementNS("http://www.w3.org/2000/svg",name);for(const [k,v] of Object.entries(attrs))n.setAttribute(k,v);return n;}
function render(){const rows=visibleSamples(),root=tree(rows),focus=locate(root,zoomPath);if(focus===root&&zoomPath.length)zoomPath=[];const total=Math.max(1,focus[metric]),plotX=145,plotW=1425,top=20,h=46,maxDepth=focus.frame==="root"?5:Math.max(1,5-zoomPath.length+1);svg.replaceChildren();
  const bg=el("rect",{x:0,y:0,width:1600,height:270,fill:"#fff"});svg.append(bg);
  const levels=focus.frame==="root"?["Outcome","Action","Phase","Subtask","Task"]:[...Array(maxDepth)].map((_,i)=>i===maxDepth-1?parts(focus.frame)[0]:"");levels.forEach((l,i)=>{const t=el("text",{x:18,y:top+i*h+27,class:"layer"});t.textContent=l;svg.append(t)});
  const nodes=[];function draw(n,x,d){const v=n[metric],w=v/total*plotW;if(w<.7)return;const y=top+(maxDepth-d)*h,[kind,label]=parts(n.frame),g=el("g",{class:"frame"});g.dataset.label=n.frame.toLowerCase();const r=el("rect",{x:x.toFixed(2),y,width:w.toFixed(2),height:h-4,rx:7,fill:color(n.frame)});g.append(r);if(w>32){const max=Math.max(3,Math.floor((w-16)/7)),shown=label.length>max?label.slice(0,max-1)+"…":label,t=el("text",{x:x+8,y:y+18,class:"frame-label",fill:textColor(n.frame)});t.textContent=shown;g.append(t);const value=fmt(v,metric);if(w>value.length*6+18){const q=el("text",{x:x+8,y:y+34,class:"frame-value",fill:textColor(n.frame)});q.textContent=value+" · "+(100*v/total).toFixed(1)+"%";g.append(q)}}
    g.addEventListener("click",()=>{zoomPath=n.path;$("reset").disabled=false;render()});g.addEventListener("mousemove",e=>{tip.style.display="block";tip.style.left=Math.min(innerWidth-460,e.clientX+14)+"px";tip.style.top=(e.clientY+14)+"px";tip.innerHTML="<b>"+n.path.map(x=>parts(x)[1]).join(" → ")+"</b><span class=muted>"+fmt(n[metric],metric)+" · "+(100*n[metric]/total).toFixed(1)+"% of current view<br>"+n.operations.toLocaleString()+" operations · "+n.tokens.toLocaleString()+" tokens</span>"});g.addEventListener("mouseleave",()=>tip.style.display="none");svg.append(g);nodes.push(g);let cx=x;[...n.children.values()].sort((a,b)=>b[metric]-a[metric]||a.frame.localeCompare(b.frame)).forEach(c=>{draw(c,cx,d+1);cx+=c[metric]/total*plotW});}
  if(focus.frame==="root"){let x=plotX;[...focus.children.values()].forEach(n=>{draw(n,x,1);x+=n[metric]/total*plotW})}else draw(focus,plotX,1);
  const query=$("search").value.trim().toLowerCase();nodes.forEach(n=>n.classList.toggle("dim",!!query&&!n.dataset.label.includes(query)));
  const ops=rows.reduce((a,s)=>a+s.operations,0),tokens=rows.reduce((a,s)=>a+s.tokens,0),agents=new Set(rows.map(s=>s.agent)).size,repeatOps=rows.filter(s=>s.repeat).reduce((a,s)=>a+s.operations,0);$("ops").textContent=ops.toLocaleString();$("tokens").textContent=tokens>=1e6?(tokens/1e6).toFixed(2)+"M":tokens.toLocaleString();$("attempts").textContent=agents;$("repeats").textContent=ops?(100*repeatOps/ops).toFixed(1)+"%":"0%";$("breadcrumbs").innerHTML="<b>Zoom:</b> "+(zoomPath.length?zoomPath.map(x=>parts(x)[1]).join(" → "):"full task");}
document.querySelectorAll(".metric").forEach(b=>b.addEventListener("click",()=>{metric=b.dataset.metric;document.querySelectorAll(".metric").forEach(x=>x.classList.toggle("active",x===b));render()}));
$("agent").addEventListener("change",()=>{zoomPath=[];$("reset").disabled=true;render()});$("issues").addEventListener("change",()=>{zoomPath=[];$("reset").disabled=true;render()});$("search").addEventListener("input",render);$("reset").addEventListener("click",()=>{zoomPath=[];$("reset").disabled=true;render()});render();
</script>
</body></html>
""".replace("__OPTIONS__", options).replace("__SAMPLES__", payload)
    path.write_text(document, encoding="utf-8")


def write_folded(path: Path, samples: list[Sample], metric: str) -> None:
    collapsed: Counter[tuple[str, ...]] = Counter()
    for sample in samples:
        collapsed[sample.stack] += sample.operations if metric == "operations" else sample.tokens
    lines = [f"{';'.join(stack)} {value}" for stack, value in sorted(collapsed.items())]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def summarize(samples: list[Sample], source: Path) -> dict[str, Any]:
    by_phase: dict[str, dict[str, int]] = {}
    for sample in samples:
        phase = frame_parts(sample.stack[2])[1]
        row = by_phase.setdefault(phase, {"operations": 0, "tokens": 0, "repeat_operations": 0})
        row["operations"] += sample.operations
        row["tokens"] += sample.tokens
        if sample.repeat:
            row["repeat_operations"] += sample.operations
    agents = sorted(set(sample.agent for sample in samples))
    failed_agents = sorted({sample.agent for sample in samples if sample.task_failed})
    return {
        "artifact_kind": "task-centric-semantic-flamegraph-shape-prototype",
        "source": str(source.relative_to(ROOT)),
        "source_task_id": SESSION,
        "task": TASK_LABEL,
        "stack_contract": ["task", "subtask", "phase", "semantic_action", "observed_outcome"],
        "stack_source_fields": ["session", "phase", "action", "repeat_state", "step_error"],
        "metric_source_fields": ["value", "input_tokens", "output_tokens"],
        "excluded_from_stack": ["agent", "model", "tool", "target", "status", "oracle/diagnostic labels"],
        "operations": sum(sample.operations for sample in samples),
        "tokens": sum(sample.tokens for sample in samples),
        "attempts": len(agents),
        "agents": agents,
        "failed_attempts": len(failed_agents),
        "repeat_operations": sum(sample.operations for sample in samples if sample.repeat),
        "action_error_operations": sum(
            sample.operations for sample in samples if frame_parts(sample.stack[-1])[1] == "Action error"
        ),
        "phase_breakdown": dict(sorted(by_phase.items())),
        "interpretation_limit": (
            "The phase-to-subtask map is declared in the generator. This artifact tests the task-centric visual shape; "
            "it does not count as evidence that task/subtask labels were inferred automatically."
        ),
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    phases = summary["phase_breakdown"]
    lines = [
        "# Task-centric semantic flamegraph prototype",
        "",
        "This artifact replaces the system-field stack with a concrete-task stack:",
        "",
        "```text",
        "task -> subtask -> phase -> semantic action -> observed outcome",
        "```",
        "",
        f"- task: `{summary['task']}`",
        f"- source task id: `{summary['source_task_id']}`",
        f"- source: `{summary['source']}`",
        f"- operations: {summary['operations']}",
        f"- input + output tokens: {summary['tokens']}",
        f"- attempts: {summary['attempts']} ({summary['failed_attempts']} failed)",
        f"- repeated operations: {summary['repeat_operations']}",
        f"- action-error operations: {summary['action_error_operations']}",
        "",
        "| Phase | Operations | Repeated operations | Tokens |",
        "|---|---:|---:|---:|",
    ]
    for phase, row in phases.items():
        lines.append(f"| {phase} | {row['operations']} | {row['repeat_operations']} | {row['tokens']} |")
    lines.extend(
        [
            "",
            "## Construction boundary",
            "",
            "The concrete task is selected by the trace session identifier. A declared `phase -> subtask` map turns source phases into readable task decomposition. The remaining frames use visible `phase`, `action`, `repeat_state`, and `step_error` fields. Agent/model identity is an interactive filter, not a stack level. Opaque DOM target IDs and oracle/diagnostic labels are excluded.",
            "",
            f"**Limit:** {summary['interpretation_limit']}",
            "",
            "Open `index.html` for metric switching, agent filtering, issue filtering, search, hover details, and click-to-zoom. The two SVG files are deterministic vector snapshots for paper/design review.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    source = args.source.resolve()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)

    samples = read_samples(source)
    write_static_svg(output / "task-centric-operations.svg", samples, "operations")
    write_static_svg(output / "task-centric-tokens.svg", samples, "tokens")
    write_folded(output / "task-centric-operations.folded", samples, "operations")
    write_folded(output / "task-centric-tokens.folded", samples, "tokens")
    write_interactive_html(output / "index.html", samples)
    summary = summarize(samples, source)
    (output / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_report(output / "report.md", summary)
    print(json.dumps({"status": "ok", "output": str(output), **summary}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

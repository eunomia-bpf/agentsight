import assert from "node:assert/strict";
import test from "node:test";
import {
  nebulaVisualMoments, repositoryNebula,
} from "./repository-nebula.js";

const helper = { base: () => ({}) };

function event(step, actions = [], extra = {}) {
  return {
    id: `event-${step}`,
    ts_ms: 1_000 + step,
    session_id: "codex:session",
    vendor: "codex",
    tool_name: actions.length ? "Edit" : "Bash",
    category: actions.length ? "file" : "process",
    command_name: actions.length ? "" : "test",
    status: "ok",
    actions,
    ...extra,
  };
}

function data(events, revision = "revision-a") {
  return {
    meta: {
      repository: "fixture",
      endpoint_revision: revision,
      window_start_ms: events[0]?.ts_ms ?? 0,
      window_end_ms: events.at(-1)?.ts_ms ?? 0,
    },
    events,
    commits: [],
  };
}

function series(option, id) {
  return option.series.find((row) => row.id === id).data;
}

test("one Tool action produces one visual moment without a total cap", () => {
  const events = Array.from({ length: 500 }, (_, step) => event(step));
  assert.equal(nebulaVisualMoments(data(events)).length, events.length + 2);
});

test("empty Tool actions preserve frames without creating file stars", () => {
  const value = data([
    event(0),
    event(1, [{ access: "create", path: "src/main.rs" }]),
  ]);
  value.meta.render_layout_step = 0;
  assert.equal(series(repositoryNebula(value, 1_000, helper), "files").length, 0);
  value.meta.render_layout_step = 1;
  assert.equal(series(repositoryNebula(value, 1_001, helper), "files").length, 1);
});

test("a recreated file clears its prior delete lifecycle", () => {
  const events = [
    event(0, [{ access: "create", path: "src/main.rs" }]),
    event(1, [{ access: "delete", path: "src/main.rs" }]),
    ...Array.from({ length: 6 }, (_, index) => event(index + 2)),
    event(8, [{ access: "create", path: "src/main.rs" }]),
  ];
  const value = data(events);
  value.meta.render_layout_step = events.length - 1;
  const files = series(repositoryNebula(value, events.at(-1).ts_ms, helper), "files");
  assert.equal(files.length, 1);
  assert.equal(files[0].lifecycleType, "create");
  assert.ok(files[0].itemStyle.opacity > 0);
});

test("Git revision does not change file colors or layout", () => {
  const events = [
    event(0, [{ access: "create", path: "src/main.rs" }]),
    event(1, [{ access: "write", path: "tests/main.rs" }]),
  ];
  const left = data(structuredClone(events), "left");
  const right = data(structuredClone(events), "right");
  left.meta.render_layout_step = 1;
  right.meta.render_layout_step = 1;
  assert.deepEqual(
    series(repositoryNebula(left, 1_001, helper), "files"),
    series(repositoryNebula(right, 1_001, helper), "files"),
  );
});

test("file actions expose one moving Agent focus without trajectory edges", () => {
  const value = data([
    event(0, [{ access: "create", path: "src/main.rs" }]),
    event(1, [{ access: "create", path: "tests/main.rs" }]),
  ]);
  value.meta.render_layout_step = 0;
  const first = series(repositoryNebula(value, 1_000, helper), "trajectory-focus");
  value.meta.render_layout_step = 1;
  const second = series(repositoryNebula(value, 1_001, helper), "trajectory-focus");
  assert.equal(first.length, 1);
  assert.equal(second.length, 1);
  assert.notDeepEqual(first[0].value, second[0].value);
  assert.ok(!repositoryNebula(value, 1_001, helper).series.some((row) => row.type === "lines"));
});

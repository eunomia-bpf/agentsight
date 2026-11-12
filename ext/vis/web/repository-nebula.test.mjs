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

function directoryLegendLabels(option) {
  const legend = option.graphic.find((group) => group.children.some((row) => (
    row.style?.text === "REPOSITORY AREAS"
  )));
  return legend.children.filter((row) => row.style?.x === 28).map((row) => row.style.text);
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

test("shell-inferred file effects are visibly weaker than direct Tool actions", () => {
  const direct = data([event(0, [{ access: "read", path: "src/main.rs" }], {
    tool_name: "Read", category: "file",
  })]);
  const shell = data([event(0, [{ access: "read", path: "src/main.rs" }], {
    tool_name: "Bash", category: "shell", command_name: "grep",
  })]);
  direct.meta.render_layout_step = 0;
  shell.meta.render_layout_step = 0;
  const directPoint = series(repositoryNebula(direct, 1_000, helper), "files")[0];
  const shellPoint = series(repositoryNebula(shell, 1_000, helper), "files")[0];
  assert.ok(directPoint.symbolSize > shellPoint.symbolSize);
});

test("directory arguments pulse descendants without creating directory stars", () => {
  const value = data([
    event(0, [{ access: "create", path: "src/main.rs" }]),
    event(1, [{ access: "create", path: "src/lib.rs" }]),
    event(2, [{ access: "create", path: "docs/readme.md" }]),
    event(3, [{ access: "read", path: "src", scope: true }], {
      tool_name: "Bash", category: "shell", command_name: "grep",
    }),
  ]);
  value.meta.render_layout_step = 3;
  const option = repositoryNebula(value, 1_003, helper);
  assert.deepEqual(series(option, "files").map((row) => row.path).sort(), [
    "docs/readme.md", "src/lib.rs", "src/main.rs",
  ]);
  assert.equal(series(option, "scope-rings").length, 2);
  assert.ok(option.graphic[0].children.some((row) => (
    row.style?.text?.includes("directory scope 0.10×")
  )));
  assert.ok(option.graphic[1].children.some((row) => row.style?.text === "REPOSITORY AREAS"));
});

test("root-level files are separate colored areas instead of a fake root directory", () => {
  const value = data([event(0, [
    { access: "create", path: "README.md" },
    { access: "create", path: "Cargo.toml" },
  ])]);
  value.meta.render_layout_step = 0;
  const option = repositoryNebula(value, 1_000, helper);
  assert.deepEqual(directoryLegendLabels(option).sort(), ["Cargo.toml", "README.md"]);
  const colors = series(option, "files").map((row) => row.itemStyle.color);
  assert.notEqual(colors[0], colors[1]);
});

test("directory legend gradually promotes the currently active directory", () => {
  const value = data([
    event(0, [{ access: "create", path: "zeta/main.rs" }]),
    event(1, [{ access: "create", path: "alpha/main.rs" }]),
    event(2, [{ access: "read", path: "alpha/main.rs" }]),
    event(3, [{ access: "read", path: "zeta/main.rs" }]),
  ]);
  value.meta.render_layout_step = 1;
  assert.deepEqual(directoryLegendLabels(repositoryNebula(value, 1_001, helper)), [
    "zeta", "alpha",
  ]);
  value.meta.render_layout_step = 2;
  assert.deepEqual(directoryLegendLabels(repositoryNebula(value, 1_002, helper)), [
    "alpha", "zeta",
  ]);
  value.meta.render_layout_step = 3;
  assert.deepEqual(directoryLegendLabels(repositoryNebula(value, 1_003, helper)), [
    "alpha", "zeta",
  ]);
});

test("directory rename preserves file identities and moves the whole subtree", () => {
  const value = data([
    event(0, [{ access: "create", path: "old/a.rs" }]),
    event(1, [{ access: "create", path: "old/sub/b.rs" }]),
    event(2, [{ access: "rename", path: "new", previous_path: "old", scope: true }], {
      tool_name: "Bash", category: "shell", command_name: "mv",
    }),
  ]);
  value.meta.render_layout_step = 2;
  assert.deepEqual(
    series(repositoryNebula(value, 1_002, helper), "files").map((row) => row.path).sort(),
    ["new/a.rs", "new/sub/b.rs"],
  );
});

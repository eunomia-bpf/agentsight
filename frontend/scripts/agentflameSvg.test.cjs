const assert = require('node:assert/strict');
const { execFileSync } = require('node:child_process');
const { readFileSync, rmSync } = require('node:fs');
const { tmpdir } = require('node:os');
const path = require('node:path');
const test = require('node:test');

const frontendRoot = path.resolve(__dirname, '..');
const repoRoot = path.resolve(frontendRoot, '..');
const outputDir = path.join(tmpdir(), `agentsight-flamegraph-test-${process.pid}`);
const compiler = path.join(frontendRoot, 'node_modules', 'typescript', 'bin', 'tsc');
const source = path.join(frontendRoot, 'src', 'utils', 'agentflameSvg.ts');

execFileSync(process.execPath, [
  compiler,
  source,
  '--target', 'es2020',
  '--module', 'commonjs',
  '--skipLibCheck',
  '--outDir', outputDir,
]);
const { parseAgentFlameSvg } = require(path.join(outputDir, 'agentflameSvg.js'));

const cases = [
  ['current Rust group format', 'docs/flamegraph/examples/public-fixture-tasks.svg', 'count', 6, 23, 'project:agentsight-public-fixture', 7],
  ['legacy semantic rect format', 'docs/visexp/out/system-flamegraph.svg', 'events', 601, 800, 'project:agentsight', 8],
  ['legacy agentpprof newline format', 'docs/visexp/out/agentpprof-svg-smoke/tools.flame.svg', 'count', 10_358, 1_639, 'project:agentsight', 8],
];

for (const [name, relative, metric, total, frames, root, deepest] of cases) {
  test(`parses ${name}`, () => {
    const profile = parseAgentFlameSvg(readFileSync(path.join(repoRoot, relative), 'utf8'));
    assert.ok(profile);
    assert.equal(profile.metric, metric);
    assert.equal(profile.total, total);
    assert.equal(profile.frames.length, frames);
    assert.equal(profile.frames.find(frame => frame.depth === 0)?.name, root);
    assert.equal(Math.max(...profile.frames.map(frame => frame.depth)), deepest);
  });
}

process.on('exit', () => rmSync(outputDir, { recursive: true, force: true }));

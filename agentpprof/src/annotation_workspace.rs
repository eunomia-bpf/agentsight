use anyhow::{Context, Result, bail};
use serde::{Deserialize, Serialize};
use serde_json::{Map, Value};
use std::collections::{BTreeMap, BTreeSet, HashMap, HashSet};
use std::fs;
use std::path::{Path, PathBuf};

use crate::profile::{Profile, ProfileView, profile_to_stacks, write_pprof_projection};

const TRACE_FILE: &str = "trace.jsonl";
const FOLDED_FILE: &str = "stacks.folded";

#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct TraceNode {
    pub id: String,
    #[serde(default)]
    pub parent: Option<String>,
    pub kind: String,
    #[serde(default)]
    pub data: Map<String, Value>,
    #[serde(default)]
    pub metrics: BTreeMap<String, u64>,
    #[serde(default)]
    pub path: Vec<String>,
}

#[derive(Clone, Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct Annotation {
    tag: String,
    parent: Option<String>,
    next: Option<String>,
}

#[derive(Clone, Debug)]
struct Region {
    start: usize,
    end: usize,
    parent: Option<usize>,
    tag: String,
}

#[derive(Clone, Debug, Serialize)]
pub struct WorkspaceSummary {
    pub annotation_file: PathBuf,
    pub trace_file: PathBuf,
    pub folded_file: PathBuf,
    pub nodes: usize,
    pub annotations: usize,
    pub samples: u64,
    pub unique_stacks: usize,
    pub max_semantic_depth: usize,
    pub warnings: Vec<String>,
}

pub fn export_annotation_workspace(
    annotation_file: &Path,
    view: ProfileView,
    output: &Path,
    deterministic_output: bool,
) -> Result<WorkspaceSummary> {
    let workspace = annotation_file.parent().unwrap_or_else(|| Path::new("."));
    let trace_file = workspace.join(TRACE_FILE);
    let folded_file = workspace.join(FOLDED_FILE);

    let raw_annotations = fs::read_to_string(annotation_file).with_context(|| {
        format!(
            "failed to read --annotation-file {}",
            annotation_file.display()
        )
    })?;
    let annotations: BTreeMap<String, Annotation> = serde_json::from_str(&raw_annotations)
        .with_context(|| format!("invalid annotation JSON in {}", annotation_file.display()))?;
    if annotations.is_empty() {
        bail!("annotation file must contain at least one tagged boundary");
    }

    let mut nodes = read_trace(&trace_file)?;
    let index = validate_source_tree(&nodes)?;
    validate_operation_scopes(&nodes, &annotations)?;
    let regions = resolve_regions(&nodes, &index, &annotations)?;
    apply_paths(&mut nodes, &regions)?;
    let warnings = hierarchy_warnings(&nodes, &regions);

    let profile = build_profile(&nodes, view)?;
    let stacks = profile_to_stacks(&profile);
    if stacks.is_empty() {
        bail!(
            "selected view produced no samples in {}",
            trace_file.display()
        );
    }

    // Build every derived artifact before replacing either workspace file.
    write_pprof_projection(&profile, output, deterministic_output)?;
    let trace_bytes = serialize_trace(&nodes)?;
    let folded_bytes = stacks
        .iter()
        .map(|(stack, value)| format!("{stack} {value}\n"))
        .collect::<String>()
        .into_bytes();
    atomic_replace(&trace_file, &trace_bytes)?;
    atomic_replace(&folded_file, &folded_bytes)?;

    Ok(WorkspaceSummary {
        annotation_file: annotation_file.to_path_buf(),
        trace_file,
        folded_file,
        nodes: nodes.len(),
        annotations: annotations.len(),
        samples: stacks.values().sum(),
        unique_stacks: stacks.len(),
        max_semantic_depth: nodes.iter().map(|node| node.path.len()).max().unwrap_or(0),
        warnings,
    })
}

fn hierarchy_warnings(nodes: &[TraceNode], regions: &[Region]) -> Vec<String> {
    let by_start = regions
        .iter()
        .enumerate()
        .map(|(region_index, region)| (region.start, region_index))
        .collect::<HashMap<_, _>>();
    let mut children = HashMap::<usize, Vec<usize>>::new();
    for (child_index, region) in regions.iter().enumerate() {
        let Some(parent_start) = region.parent else {
            continue;
        };
        if let Some(parent_index) = by_start.get(&parent_start).copied() {
            children.entry(parent_index).or_default().push(child_index);
        }
    }

    let mut warnings = BTreeSet::new();
    for (region_index, region) in regions.iter().enumerate() {
        let direct_children = children
            .get(&region_index)
            .map(Vec::as_slice)
            .unwrap_or(&[]);
        let source_kind = nodes[region.start].kind.as_str();
        if source_kind != "session" && source_kind != "prompt" && direct_children.len() == 1 {
            warnings.insert(format!(
                "degenerate unary refinement: operation {:?} at {:?} has only one explicit semantic child",
                region.tag, nodes[region.start].id
            ));
        }

        let covered_tool_calls = nodes[region.start..region.end]
            .iter()
            .filter(|node| node.kind == "tool")
            .count();
        if source_kind != "session"
            && source_kind != "prompt"
            && direct_children.is_empty()
            && covered_tool_calls >= 8
        {
            warnings.insert(format!(
                "coarse unrefined span: operation {:?} at {:?} covers {} tool calls without a semantic child",
                region.tag, nodes[region.start].id, covered_tool_calls
            ));
        }

        if direct_children.len() >= 8 {
            let refined_children = direct_children
                .iter()
                .filter(|child| children.get(child).is_some_and(|nested| !nested.is_empty()))
                .count();
            if refined_children * 4 < direct_children.len() {
                warnings.insert(format!(
                    "flat fan-out: operation {:?} at {:?} has {} direct semantic children but only {} recursively refined children",
                    region.tag,
                    nodes[region.start].id,
                    direct_children.len(),
                    refined_children
                ));
            }
        }
    }
    warnings.into_iter().collect()
}

fn read_trace(path: &Path) -> Result<Vec<TraceNode>> {
    let raw = fs::read_to_string(path)
        .with_context(|| format!("failed to read workspace trace {}", path.display()))?;
    let mut nodes = Vec::new();
    for (line_index, line) in raw.lines().enumerate() {
        if line.trim().is_empty() {
            continue;
        }
        let node: TraceNode = serde_json::from_str(line).with_context(|| {
            format!(
                "invalid trace node at {}:{}",
                path.display(),
                line_index + 1
            )
        })?;
        nodes.push(node);
    }
    if nodes.is_empty() {
        bail!("workspace trace {} is empty", path.display());
    }
    Ok(nodes)
}

fn validate_source_tree(nodes: &[TraceNode]) -> Result<HashMap<String, usize>> {
    let mut index = HashMap::new();
    for (position, node) in nodes.iter().enumerate() {
        if node.id.trim().is_empty() || node.kind.trim().is_empty() {
            bail!("trace node {} has an empty id or kind", position + 1);
        }
        if index.insert(node.id.clone(), position).is_some() {
            bail!("duplicate trace node id {:?}", node.id);
        }
        if let Some(parent) = node.parent.as_ref()
            && !index.contains_key(parent)
        {
            bail!(
                "trace node {:?} refers to missing or later parent {:?}",
                node.id,
                parent
            );
        }
    }
    Ok(index)
}

fn validate_operation_scopes(
    nodes: &[TraceNode],
    annotations: &BTreeMap<String, Annotation>,
) -> Result<()> {
    for node in nodes {
        if node.parent.is_none() && !annotations.contains_key(&node.id) {
            bail!(
                "source root {:?} must begin a session-level operation",
                node.id
            );
        }
        if node.kind == "prompt" && !annotations.contains_key(&node.id) {
            bail!(
                "prompt node {:?} must begin a prompt-level operation",
                node.id
            );
        }
    }
    Ok(())
}

fn resolve_regions(
    nodes: &[TraceNode],
    index: &HashMap<String, usize>,
    annotations: &BTreeMap<String, Annotation>,
) -> Result<Vec<Region>> {
    let mut session_end = vec![nodes.len(); nodes.len()];
    let mut active_root = None;
    for (position, node) in nodes.iter().enumerate() {
        if node.parent.is_none() {
            if let Some(root) = active_root.replace(position) {
                session_end[root] = position;
            }
        }
    }
    if let Some(root) = active_root {
        session_end[root] = nodes.len();
    }

    let mut root_for_node = vec![0; nodes.len()];
    let mut current_root = None;
    for (position, node) in nodes.iter().enumerate() {
        if node.parent.is_none() {
            current_root = Some(position);
        }
        root_for_node[position] = current_root
            .with_context(|| format!("trace node {:?} appears before a root node", node.id))?;
    }

    let mut starts = HashMap::new();
    for (id, annotation) in annotations {
        let tag = annotation.tag.trim();
        if tag.is_empty() {
            bail!("annotation at {:?} has an empty tag", id);
        }
        let words = tag.split_whitespace().count();
        if words > 3 {
            bail!(
                "annotation at {:?} has {} words; operation tags must contain 1 to 3 words",
                id,
                words
            );
        }
        let start = *index
            .get(id)
            .with_context(|| format!("annotation refers to unknown start node {id:?}"))?;
        starts.insert(id.clone(), start);
    }

    let mut regions = Vec::with_capacity(annotations.len());
    let mut region_by_start = HashMap::new();
    for (id, annotation) in annotations {
        let start = starts[id];
        let parent_start = annotation
            .parent
            .as_ref()
            .map(|parent| {
                starts.get(parent).copied().with_context(|| {
                    format!("annotation at {id:?} refers to unknown semantic parent {parent:?}")
                })
            })
            .transpose()?;
        if parent_start == Some(start) {
            bail!("annotation at {id:?} cannot be its own semantic parent");
        }
        let explicit_end = annotation
            .next
            .as_ref()
            .map(|next| {
                index.get(next).copied().with_context(|| {
                    format!("annotation at {id:?} refers to unknown next node {next:?}")
                })
            })
            .transpose()?;
        let root = root_for_node[start];
        if parent_start.is_none() && nodes[start].parent.is_some() {
            bail!(
                "root annotation at {:?} must start at a source root; add its semantic parent",
                id
            );
        }
        if parent_start.is_none() && start != root {
            bail!("root annotation at {id:?} does not start at its session root");
        }
        if let Some(end) = explicit_end {
            if end <= start {
                bail!("annotation at {id:?} has a non-forward next boundary");
            }
            if root_for_node[end] != root {
                bail!("annotation at {id:?} crosses a session boundary");
            }
        }
        let region_index = regions.len();
        regions.push(Region {
            start,
            end: explicit_end.unwrap_or(session_end[root]),
            parent: parent_start,
            tag: annotation.tag.trim().to_string(),
        });
        region_by_start.insert(start, region_index);
    }

    for region_index in 0..regions.len() {
        let parent_start = regions[region_index].parent;
        let parent_index = parent_start
            .map(|start| {
                region_by_start.get(&start).copied().with_context(|| {
                    format!(
                        "semantic parent starting at {:?} is not an annotation",
                        nodes[start].id
                    )
                })
            })
            .transpose()?;
        if regions[region_index].end == session_end[root_for_node[regions[region_index].start]] {
            if let Some(parent_index) = parent_index {
                regions[region_index].end = regions[parent_index].end;
            }
        }
        if let Some(parent_index) = parent_index {
            let child = &regions[region_index];
            let parent = &regions[parent_index];
            if child.start < parent.start || child.end > parent.end {
                bail!(
                    "annotation {:?} is not contained by semantic parent {:?}",
                    nodes[child.start].id,
                    nodes[parent.start].id
                );
            }
        }
    }

    for left in 0..regions.len() {
        for right in (left + 1)..regions.len() {
            let a = &regions[left];
            let b = &regions[right];
            let overlaps = a.start < b.end && b.start < a.end;
            let nested =
                (a.start <= b.start && b.end <= a.end) || (b.start <= a.start && a.end <= b.end);
            if overlaps && !nested {
                bail!(
                    "annotations at {:?} and {:?} cross; ranges must be nested or disjoint",
                    nodes[a.start].id,
                    nodes[b.start].id
                );
            }
        }
    }
    Ok(regions)
}

fn apply_paths(nodes: &mut [TraceNode], regions: &[Region]) -> Result<()> {
    let by_start = regions
        .iter()
        .enumerate()
        .map(|(region_index, region)| (region.start, region_index))
        .collect::<HashMap<_, _>>();
    for (position, node) in nodes.iter_mut().enumerate() {
        let mut containing = regions
            .iter()
            .enumerate()
            .filter(|(_, region)| region.start <= position && position < region.end)
            .map(|(region_index, _)| region_index)
            .collect::<Vec<_>>();
        containing.sort_by_key(|region_index| semantic_depth(*region_index, regions, &by_start));
        node.path = containing
            .into_iter()
            .map(|region_index| regions[region_index].tag.clone())
            .collect();
        if node.path.is_empty() {
            bail!("trace node {:?} is not covered by a semantic root", node.id);
        }
    }
    Ok(())
}

fn semantic_depth(
    mut region_index: usize,
    regions: &[Region],
    by_start: &HashMap<usize, usize>,
) -> usize {
    let mut depth = 0;
    let mut seen = HashSet::new();
    while seen.insert(region_index) {
        depth += 1;
        let Some(parent_start) = regions[region_index].parent else {
            break;
        };
        let Some(parent_index) = by_start.get(&parent_start).copied() else {
            break;
        };
        region_index = parent_index;
    }
    depth
}

fn build_profile(nodes: &[TraceNode], view: ProfileView) -> Result<Profile> {
    let (view_name, sample_type, unit, metric) = match view {
        ProfileView::Operations => ("operations", "operations", "count", "operations"),
        ProfileView::Tokens => ("tokens", "tokens", "count", "tokens"),
        ProfileView::Files => ("files", "file_events", "count", "files"),
        ProfileView::Network => ("network", "network_events", "count", "network"),
        ProfileView::Time => ("time", "duration", "nanoseconds", "time_ns"),
    };
    let mut profile = Profile::new(view_name, sample_type, unit);
    let index = nodes
        .iter()
        .enumerate()
        .map(|(position, node)| (node.id.as_str(), position))
        .collect::<HashMap<_, _>>();
    for node in nodes {
        let value = node.metrics.get(metric).copied().unwrap_or(0);
        if value == 0 {
            continue;
        }
        let ancestry = source_ancestry(node, nodes, &index)?;
        let mut frames = Vec::new();
        if let Some(agent) = ancestry
            .iter()
            .find_map(|source| source.data.get("agent").and_then(Value::as_str))
            .filter(|value| !value.trim().is_empty())
        {
            frames.push(("agent".to_string(), agent.to_string()));
        }
        frames.extend(
            node.path
                .iter()
                .map(|tag| ("operation".to_string(), tag.clone())),
        );
        for source in ancestry
            .iter()
            .filter(|source| source.kind != "session" && source.kind != "prompt")
        {
            frames.push(source_frame(source));
        }
        let session = ancestry
            .iter()
            .find(|source| source.parent.is_none())
            .map(|source| source.id.clone())
            .unwrap_or_else(|| "unknown".to_string());
        let labels = vec![
            ("source_session".to_string(), session),
            (
                "source_prompt".to_string(),
                ancestry
                    .iter()
                    .find(|source| source.kind == "prompt")
                    .map(|source| source.id.clone())
                    .unwrap_or_else(|| "unknown".to_string()),
            ),
            ("source_kind".to_string(), node.kind.clone()),
            ("evidence_id".to_string(), node.id.clone()),
        ];
        profile.sample(frames, value, labels);
    }
    Ok(profile)
}

fn source_ancestry<'a>(
    node: &'a TraceNode,
    nodes: &'a [TraceNode],
    index: &HashMap<&str, usize>,
) -> Result<Vec<&'a TraceNode>> {
    let mut ancestry = vec![node];
    let mut current = node;
    while let Some(parent) = current.parent.as_deref() {
        current = &nodes[*index.get(parent).with_context(|| {
            format!("trace node {:?} has unknown parent {parent:?}", current.id)
        })?];
        ancestry.push(current);
    }
    ancestry.reverse();
    Ok(ancestry)
}

fn source_frame(node: &TraceNode) -> (String, String) {
    let label = ["name", "tool", "title"]
        .iter()
        .find_map(|key| node.data.get(*key).and_then(Value::as_str))
        .filter(|value| !value.trim().is_empty())
        .unwrap_or(&node.id);
    (node.kind.clone(), label.to_string())
}

fn serialize_trace(nodes: &[TraceNode]) -> Result<Vec<u8>> {
    let mut out = Vec::new();
    for node in nodes {
        serde_json::to_writer(&mut out, node)?;
        out.push(b'\n');
    }
    Ok(out)
}

fn atomic_replace(path: &Path, content: &[u8]) -> Result<()> {
    let file_name = path
        .file_name()
        .and_then(|name| name.to_str())
        .unwrap_or("workspace-file");
    let temporary = path.with_file_name(format!(".{file_name}.tmp-{}", std::process::id()));
    fs::write(&temporary, content)
        .with_context(|| format!("failed to write temporary file {}", temporary.display()))?;
    fs::rename(&temporary, path)
        .with_context(|| format!("failed to replace {}", path.display()))?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    fn nodes() -> Vec<TraceNode> {
        [
            ("s", None, "session", 0),
            ("p", Some("s"), "prompt", 0),
            ("c1", Some("p"), "llm", 0),
            ("t1", Some("c1"), "tool", 3),
            ("c2", Some("p"), "llm", 0),
            ("t2", Some("c2"), "tool", 5),
        ]
        .into_iter()
        .map(|(id, parent, kind, operations)| TraceNode {
            id: id.to_string(),
            parent: parent.map(str::to_string),
            kind: kind.to_string(),
            data: Map::new(),
            metrics: if operations == 0 {
                BTreeMap::new()
            } else {
                BTreeMap::from([("operations".to_string(), operations)])
            },
            path: Vec::new(),
        })
        .collect()
    }

    #[test]
    fn nested_and_sibling_annotations_produce_variable_depth_paths() {
        let mut nodes = nodes();
        let index = validate_source_tree(&nodes).unwrap();
        let annotations = BTreeMap::from([
            (
                "s".to_string(),
                Annotation {
                    tag: "Repair".to_string(),
                    parent: None,
                    next: None,
                },
            ),
            (
                "p".to_string(),
                Annotation {
                    tag: "Fix reported regression".to_string(),
                    parent: Some("s".to_string()),
                    next: None,
                },
            ),
            (
                "c1".to_string(),
                Annotation {
                    tag: "Diagnose".to_string(),
                    parent: Some("p".to_string()),
                    next: Some("c2".to_string()),
                },
            ),
            (
                "t1".to_string(),
                Annotation {
                    tag: "Run reproducer".to_string(),
                    parent: Some("c1".to_string()),
                    next: Some("c2".to_string()),
                },
            ),
            (
                "c2".to_string(),
                Annotation {
                    tag: "Fix".to_string(),
                    parent: Some("p".to_string()),
                    next: None,
                },
            ),
        ]);
        let regions = resolve_regions(&nodes, &index, &annotations).unwrap();
        apply_paths(&mut nodes, &regions).unwrap();
        assert_eq!(
            nodes[3].path,
            [
                "Repair",
                "Fix reported regression",
                "Diagnose",
                "Run reproducer"
            ]
        );
        assert_eq!(nodes[5].path, ["Repair", "Fix reported regression", "Fix"]);
    }

    #[test]
    fn wide_unrefined_prompt_emits_flat_fanout_warning() {
        let mut nodes = vec![
            TraceNode {
                id: "s".to_string(),
                parent: None,
                kind: "session".to_string(),
                data: Map::new(),
                metrics: BTreeMap::new(),
                path: Vec::new(),
            },
            TraceNode {
                id: "p".to_string(),
                parent: Some("s".to_string()),
                kind: "prompt".to_string(),
                data: Map::new(),
                metrics: BTreeMap::new(),
                path: Vec::new(),
            },
        ];
        let mut annotations = BTreeMap::from([
            (
                "s".to_string(),
                Annotation {
                    tag: "Task".to_string(),
                    parent: None,
                    next: None,
                },
            ),
            (
                "p".to_string(),
                Annotation {
                    tag: "Request".to_string(),
                    parent: Some("s".to_string()),
                    next: None,
                },
            ),
        ]);
        for child in 0..8 {
            let id = format!("c{child}");
            nodes.push(TraceNode {
                id: id.clone(),
                parent: Some("p".to_string()),
                kind: "llm".to_string(),
                data: Map::new(),
                metrics: BTreeMap::new(),
                path: Vec::new(),
            });
            annotations.insert(
                id,
                Annotation {
                    tag: format!("Child {child}"),
                    parent: Some("p".to_string()),
                    next: (child < 7).then(|| format!("c{}", child + 1)),
                },
            );
        }

        let index = validate_source_tree(&nodes).unwrap();
        let regions = resolve_regions(&nodes, &index, &annotations).unwrap();
        let warnings = hierarchy_warnings(&nodes, &regions);
        assert!(
            warnings
                .iter()
                .any(|warning| warning.contains("flat fan-out"))
        );
    }

    #[test]
    fn crossing_annotations_are_rejected() {
        let nodes = nodes();
        let index = validate_source_tree(&nodes).unwrap();
        let annotations = BTreeMap::from([
            (
                "s".to_string(),
                Annotation {
                    tag: "Repair".to_string(),
                    parent: None,
                    next: None,
                },
            ),
            (
                "c1".to_string(),
                Annotation {
                    tag: "A".to_string(),
                    parent: Some("s".to_string()),
                    next: Some("t2".to_string()),
                },
            ),
            (
                "t1".to_string(),
                Annotation {
                    tag: "B".to_string(),
                    parent: Some("s".to_string()),
                    next: None,
                },
            ),
        ]);
        let error = resolve_regions(&nodes, &index, &annotations)
            .unwrap_err()
            .to_string();
        assert!(error.contains("cross") || error.contains("contained"));
    }

    #[test]
    fn every_source_node_must_be_covered_by_an_operation() {
        let mut nodes = nodes();
        nodes.push(TraceNode {
            id: "s2".to_string(),
            parent: None,
            kind: "session".to_string(),
            data: Map::new(),
            metrics: BTreeMap::new(),
            path: Vec::new(),
        });
        nodes.push(TraceNode {
            id: "p2".to_string(),
            parent: Some("s2".to_string()),
            kind: "prompt".to_string(),
            data: Map::new(),
            metrics: BTreeMap::new(),
            path: Vec::new(),
        });
        let index = validate_source_tree(&nodes).unwrap();
        let annotations = BTreeMap::from([(
            "s".to_string(),
            Annotation {
                tag: "Repair".to_string(),
                parent: None,
                next: None,
            },
        )]);
        let regions = resolve_regions(&nodes, &index, &annotations).unwrap();
        let error = apply_paths(&mut nodes, &regions).unwrap_err().to_string();
        assert_eq!(error, "trace node \"s2\" is not covered by a semantic root");
    }

    #[test]
    fn every_prompt_must_begin_a_prompt_level_operation() {
        let nodes = nodes();
        let annotations = BTreeMap::from([(
            "s".to_string(),
            Annotation {
                tag: "Repair".to_string(),
                parent: None,
                next: None,
            },
        )]);
        let error = validate_operation_scopes(&nodes, &annotations)
            .unwrap_err()
            .to_string();
        assert_eq!(
            error,
            "prompt node \"p\" must begin a prompt-level operation"
        );
    }
}

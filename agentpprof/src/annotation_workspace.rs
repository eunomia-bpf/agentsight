use anyhow::{Context, Result, bail};
use serde::{Deserialize, Serialize};
use serde_json::{Map, Value};
use std::collections::{BTreeMap, BTreeSet, HashMap, HashSet};
use std::fs;
use std::path::{Path, PathBuf};

use crate::profile::{Profile, ProfileView, profile_to_stacks, safe_frame, write_pprof_projection};

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
    pub semantic_tags: usize,
    pub cross_session_tags: usize,
    pub singleton_tags: usize,
    pub min_semantic_depth: usize,
    pub max_semantic_depth: usize,
    pub semantic_depth_mass: BTreeMap<usize, u64>,
    pub tag_reuse: Vec<TagReuseSummary>,
    pub near_name_candidates: Vec<NearNameCandidate>,
    pub issues: Vec<HierarchyIssue>,
    pub warnings: Vec<String>,
}

#[derive(Clone, Debug, Serialize)]
pub struct TagReuseSummary {
    pub tag: String,
    pub occurrences: usize,
    pub sessions: Vec<String>,
}

#[derive(Clone, Debug, Serialize)]
pub struct NearNameCandidate {
    pub left: String,
    pub right: String,
    pub edit_distance: usize,
}

#[derive(Clone, Debug, Serialize)]
pub struct HierarchyIssue {
    pub kind: String,
    pub tag: String,
    pub start_node_id: String,
    pub end_node_id: Option<String>,
    pub session_id: String,
    pub covered_tool_calls: usize,
    pub direct_children: usize,
    pub refined_children: usize,
}

#[derive(Debug)]
struct HierarchyDiagnostics {
    semantic_tags: usize,
    cross_session_tags: usize,
    singleton_tags: usize,
    min_semantic_depth: usize,
    max_semantic_depth: usize,
    semantic_depth_mass: BTreeMap<usize, u64>,
    tag_reuse: Vec<TagReuseSummary>,
    near_name_candidates: Vec<NearNameCandidate>,
    issues: Vec<HierarchyIssue>,
    warnings: Vec<String>,
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
    let diagnostics = hierarchy_diagnostics(&nodes, &regions, view);

    let profile = build_profile(&nodes, view)?;
    let stacks = profile_to_stacks(&profile);
    if stacks.is_empty() {
        bail!(
            "selected view produced no samples in {}",
            trace_file.display()
        );
    }
    let sample_mass = stacks.values().sum::<u64>();
    let depth_mass = diagnostics.semantic_depth_mass.values().sum::<u64>();
    if depth_mass != sample_mass {
        bail!(
            "annotation workspace depth mass {depth_mass} does not match pprof sample mass {sample_mass}"
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
        samples: sample_mass,
        unique_stacks: stacks.len(),
        semantic_tags: diagnostics.semantic_tags,
        cross_session_tags: diagnostics.cross_session_tags,
        singleton_tags: diagnostics.singleton_tags,
        min_semantic_depth: diagnostics.min_semantic_depth,
        max_semantic_depth: diagnostics.max_semantic_depth,
        semantic_depth_mass: diagnostics.semantic_depth_mass,
        tag_reuse: diagnostics.tag_reuse,
        near_name_candidates: diagnostics.near_name_candidates,
        issues: diagnostics.issues,
        warnings: diagnostics.warnings,
    })
}

fn hierarchy_diagnostics(
    nodes: &[TraceNode],
    regions: &[Region],
    view: ProfileView,
) -> HierarchyDiagnostics {
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

    let mut root_at = vec![0; nodes.len()];
    let mut root = 0;
    let mut roots = 0;
    for (position, node) in nodes.iter().enumerate() {
        if node.parent.is_none() {
            root = position;
            roots += 1;
        }
        root_at[position] = root;
    }

    let mut warnings = BTreeSet::new();
    let mut issues = Vec::new();
    for (region_index, region) in regions.iter().enumerate() {
        let direct_children = children
            .get(&region_index)
            .map(Vec::as_slice)
            .unwrap_or(&[]);
        let refined_children = direct_children
            .iter()
            .filter(|child| children.get(child).is_some_and(|nested| !nested.is_empty()))
            .count();
        let source_kind = nodes[region.start].kind.as_str();
        let covered_tool_calls = nodes[region.start..region.end]
            .iter()
            .filter(|node| node.kind == "tool")
            .count();
        let end_node_id = nodes.get(region.end).map(|node| node.id.clone());
        let issue = |kind: &str| HierarchyIssue {
            kind: kind.to_string(),
            tag: region.tag.clone(),
            start_node_id: nodes[region.start].id.clone(),
            end_node_id: end_node_id.clone(),
            session_id: nodes[root_at[region.start]].id.clone(),
            covered_tool_calls,
            direct_children: direct_children.len(),
            refined_children,
        };
        if source_kind != "session" && source_kind != "prompt" && direct_children.len() == 1 {
            warnings.insert(format!(
                "degenerate unary refinement: operation {:?} at {:?} has only one explicit semantic child",
                region.tag, nodes[region.start].id
            ));
            issues.push(issue("unary_refinement"));
        }

        if source_kind != "session"
            && source_kind != "prompt"
            && direct_children.is_empty()
            && covered_tool_calls >= 8
        {
            warnings.insert(format!(
                "coarse unrefined span: operation {:?} at {:?} covers {} tool calls without a semantic child",
                region.tag, nodes[region.start].id, covered_tool_calls
            ));
            issues.push(issue("coarse_span"));
        }

        if direct_children.len() >= 8 && refined_children * 4 < direct_children.len() {
            warnings.insert(format!(
                "flat fan-out: operation {:?} at {:?} has {} direct semantic children but only {} recursively refined children",
                region.tag,
                nodes[region.start].id,
                direct_children.len(),
                refined_children
            ));
            issues.push(issue("flat_fanout"));
        }
    }

    let mut tag_sessions = BTreeMap::<String, BTreeSet<String>>::new();
    let mut tag_occurrences = BTreeMap::<String, usize>::new();
    for region in regions {
        let source_kind = nodes[region.start].kind.as_str();
        if source_kind == "session" || source_kind == "prompt" {
            continue;
        }
        let tag = safe_frame(&region.tag, Some("operation"))
            .strip_prefix("operation:")
            .unwrap_or(&region.tag)
            .replace('_', " ");
        tag_sessions
            .entry(tag.clone())
            .or_default()
            .insert(nodes[root_at[region.start]].id.clone());
        *tag_occurrences.entry(tag).or_default() += 1;
    }
    let tag_reuse = tag_sessions
        .iter()
        .map(|(tag, sessions)| TagReuseSummary {
            tag: tag.clone(),
            occurrences: tag_occurrences.get(tag).copied().unwrap_or(0),
            sessions: sessions.iter().cloned().collect(),
        })
        .collect::<Vec<_>>();
    let semantic_tags = tag_sessions.len();
    let cross_session_tags = tag_sessions
        .values()
        .filter(|sessions| sessions.len() > 1)
        .count();
    let singleton_names = tag_sessions
        .iter()
        .filter(|(_, sessions)| sessions.len() == 1)
        .map(|(tag, _)| tag.clone())
        .collect::<Vec<_>>();
    let singleton_tags = singleton_names.len();
    if roots > 1 && singleton_tags > 0 {
        let examples = singleton_names
            .iter()
            .take(5)
            .cloned()
            .collect::<Vec<_>>()
            .join(", ");
        warnings.insert(format!(
            "cross-session fragmentation: {singleton_tags} of {semantic_tags} optional operation tags appear in only one session; examples: {examples}"
        ));
    }

    let names = tag_sessions.keys().cloned().collect::<Vec<_>>();
    let near_name_candidates = find_near_name_candidates(&names);
    if !near_name_candidates.is_empty() {
        let examples = near_name_candidates
            .iter()
            .take(5)
            .map(|candidate| format!("{} ~ {}", candidate.left, candidate.right))
            .collect::<Vec<_>>()
            .join(", ");
        warnings.insert(format!(
            "lexically near operation tags: inspect before keeping separate or merging; examples: {examples}"
        ));
    }

    let metric = match view {
        ProfileView::Operations => "operations",
        ProfileView::Tokens => "tokens",
        ProfileView::Files => "files",
        ProfileView::Network => "network",
        ProfileView::Time => "time_ns",
    };
    let mut semantic_depth_mass = BTreeMap::<usize, u64>::new();
    for node in nodes {
        let weight = node.metrics.get(metric).copied().unwrap_or(0);
        if weight > 0 {
            *semantic_depth_mass.entry(node.path.len()).or_default() += weight;
        }
    }
    let min_semantic_depth = semantic_depth_mass.keys().next().copied().unwrap_or(0);
    let max_semantic_depth = semantic_depth_mass.keys().next_back().copied().unwrap_or(0);
    if max_semantic_depth.saturating_sub(min_semantic_depth) >= 4 {
        warnings.insert(format!(
            "uneven semantic depth: weighted leaves range from {min_semantic_depth} to {max_semantic_depth} operation frames"
        ));
    }

    HierarchyDiagnostics {
        semantic_tags,
        cross_session_tags,
        singleton_tags,
        min_semantic_depth,
        max_semantic_depth,
        semantic_depth_mass,
        tag_reuse,
        near_name_candidates,
        issues,
        warnings: warnings.into_iter().collect(),
    }
}

fn find_near_name_candidates(names: &[String]) -> Vec<NearNameCandidate> {
    let mut candidates = Vec::new();
    for (left_index, left) in names.iter().enumerate() {
        for right in names.iter().skip(left_index + 1) {
            if left.chars().count().abs_diff(right.chars().count()) > 2 {
                continue;
            }
            let edit_distance = levenshtein_distance(left, right);
            if edit_distance > 0 && edit_distance <= 2 {
                candidates.push(NearNameCandidate {
                    left: left.clone(),
                    right: right.clone(),
                    edit_distance,
                });
            }
        }
    }
    candidates
}

fn levenshtein_distance(left: &str, right: &str) -> usize {
    let right = right.chars().collect::<Vec<_>>();
    let mut previous = (0..=right.len()).collect::<Vec<_>>();
    for (left_index, left_char) in left.chars().enumerate() {
        let mut current = Vec::with_capacity(right.len() + 1);
        current.push(left_index + 1);
        for (right_index, right_char) in right.iter().enumerate() {
            let substitution = previous[right_index] + usize::from(left_char != *right_char);
            let insertion = current[right_index] + 1;
            let deletion = previous[right_index + 1] + 1;
            current.push(substitution.min(insertion).min(deletion));
        }
        previous = current;
    }
    previous[right.len()]
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
    let (root_for_node, session_end) = source_root_layout(nodes, index)?;

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
    let mut explicit_ends = Vec::with_capacity(annotations.len());
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
            end: explicit_end.unwrap_or(0),
            parent: parent_start,
            tag: annotation.tag.trim().to_string(),
        });
        explicit_ends.push(explicit_end);
        region_by_start.insert(start, region_index);
    }

    let mut parent_indices = Vec::with_capacity(regions.len());
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
        if let Some(parent_index) = parent_index
            && root_for_node[regions[parent_index].start]
                != root_for_node[regions[region_index].start]
        {
            bail!(
                "annotation {:?} has semantic parent {:?} in another session",
                nodes[regions[region_index].start].id,
                nodes[regions[parent_index].start].id
            );
        }
        parent_indices.push(parent_index);
    }

    let mut end_state = vec![0_u8; regions.len()];
    for region_index in 0..regions.len() {
        resolve_region_end(
            region_index,
            &mut regions,
            &explicit_ends,
            &parent_indices,
            &root_for_node,
            &session_end,
            nodes,
            &mut end_state,
        )?;
    }

    for region_index in 0..regions.len() {
        let parent_index = parent_indices[region_index];
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
            let a_contains_b = a.start <= b.start && b.end <= a.end;
            let b_contains_a = b.start <= a.start && a.end <= b.end;
            if overlaps && !a_contains_b && !b_contains_a {
                bail!(
                    "annotations at {:?} and {:?} cross; ranges must be nested or disjoint",
                    nodes[a.start].id,
                    nodes[b.start].id
                );
            }
            if a_contains_b && !is_semantic_ancestor(left, right, &parent_indices) {
                bail!(
                    "annotation {:?} is nested inside {:?} but does not declare it as a semantic ancestor",
                    nodes[b.start].id,
                    nodes[a.start].id
                );
            }
            if b_contains_a && !is_semantic_ancestor(right, left, &parent_indices) {
                bail!(
                    "annotation {:?} is nested inside {:?} but does not declare it as a semantic ancestor",
                    nodes[a.start].id,
                    nodes[b.start].id
                );
            }
        }
    }
    Ok(regions)
}

fn source_root_layout(
    nodes: &[TraceNode],
    index: &HashMap<String, usize>,
) -> Result<(Vec<usize>, Vec<usize>)> {
    let mut root_for_node = vec![0; nodes.len()];
    for (position, node) in nodes.iter().enumerate() {
        root_for_node[position] = match node.parent.as_ref() {
            None => position,
            Some(parent) => root_for_node[index[parent]],
        };
    }

    let mut session_end = vec![nodes.len(); nodes.len()];
    let mut previous_root = None;
    let mut closed_roots = HashSet::new();
    for (position, root) in root_for_node.iter().copied().enumerate() {
        if previous_root == Some(root) {
            continue;
        }
        if closed_roots.contains(&root) {
            bail!(
                "trace node {:?} returns to an earlier source root; each session must be one contiguous source-tree block",
                nodes[position].id
            );
        }
        if let Some(previous) = previous_root {
            session_end[previous] = position;
            closed_roots.insert(previous);
        }
        previous_root = Some(root);
    }
    if let Some(root) = previous_root {
        session_end[root] = nodes.len();
    }
    Ok((root_for_node, session_end))
}

#[allow(clippy::too_many_arguments)]
fn resolve_region_end(
    region_index: usize,
    regions: &mut [Region],
    explicit_ends: &[Option<usize>],
    parent_indices: &[Option<usize>],
    root_for_node: &[usize],
    session_end: &[usize],
    nodes: &[TraceNode],
    state: &mut [u8],
) -> Result<usize> {
    match state[region_index] {
        2 => return Ok(regions[region_index].end),
        1 => {
            bail!(
                "annotation {:?} participates in a semantic-parent cycle",
                nodes[regions[region_index].start].id
            )
        }
        _ => {}
    }
    state[region_index] = 1;
    let end = if let Some(end) = explicit_ends[region_index] {
        end
    } else if let Some(parent_index) = parent_indices[region_index] {
        resolve_region_end(
            parent_index,
            regions,
            explicit_ends,
            parent_indices,
            root_for_node,
            session_end,
            nodes,
            state,
        )?
    } else {
        session_end[root_for_node[regions[region_index].start]]
    };
    if end <= regions[region_index].start {
        bail!(
            "annotation at {:?} resolves to a non-forward end boundary",
            nodes[regions[region_index].start].id
        );
    }
    regions[region_index].end = end;
    state[region_index] = 2;
    Ok(end)
}

fn is_semantic_ancestor(
    candidate: usize,
    descendant: usize,
    parent_indices: &[Option<usize>],
) -> bool {
    let mut current = parent_indices[descendant];
    while let Some(region_index) = current {
        if region_index == candidate {
            return true;
        }
        current = parent_indices[region_index];
    }
    false
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
    fn inherited_ends_follow_semantic_parents_not_annotation_key_order() {
        let mut nodes = [
            ("s", None, "session"),
            ("p", Some("s"), "prompt"),
            ("z_grand", Some("p"), "llm"),
            ("y_parent", Some("p"), "llm"),
            ("a_child", Some("p"), "llm"),
            ("end", Some("p"), "llm"),
        ]
        .into_iter()
        .map(|(id, parent, kind)| TraceNode {
            id: id.to_string(),
            parent: parent.map(str::to_string),
            kind: kind.to_string(),
            data: Map::new(),
            metrics: BTreeMap::from([("operations".to_string(), 1)]),
            path: Vec::new(),
        })
        .collect::<Vec<_>>();
        let index = validate_source_tree(&nodes).unwrap();
        let annotations = BTreeMap::from([
            (
                "s".to_string(),
                Annotation {
                    tag: "Execute".to_string(),
                    parent: None,
                    next: None,
                },
            ),
            (
                "p".to_string(),
                Annotation {
                    tag: "Fulfill request".to_string(),
                    parent: Some("s".to_string()),
                    next: None,
                },
            ),
            (
                "z_grand".to_string(),
                Annotation {
                    tag: "Inspect".to_string(),
                    parent: Some("p".to_string()),
                    next: Some("end".to_string()),
                },
            ),
            (
                "y_parent".to_string(),
                Annotation {
                    tag: "Diagnose".to_string(),
                    parent: Some("z_grand".to_string()),
                    next: None,
                },
            ),
            (
                "a_child".to_string(),
                Annotation {
                    tag: "Test".to_string(),
                    parent: Some("y_parent".to_string()),
                    next: None,
                },
            ),
            (
                "end".to_string(),
                Annotation {
                    tag: "Report".to_string(),
                    parent: Some("p".to_string()),
                    next: None,
                },
            ),
        ]);
        let regions = resolve_regions(&nodes, &index, &annotations).unwrap();
        apply_paths(&mut nodes, &regions).unwrap();
        assert_eq!(
            nodes[4].path,
            ["Execute", "Fulfill request", "Inspect", "Diagnose", "Test"]
        );
    }

    #[test]
    fn nested_intervals_declared_as_siblings_are_rejected() {
        let nodes = [
            ("s", None, "session"),
            ("p", Some("s"), "prompt"),
            ("c1", Some("p"), "llm"),
            ("c2", Some("p"), "llm"),
            ("c3", Some("p"), "llm"),
            ("c4", Some("p"), "llm"),
        ]
        .into_iter()
        .map(|(id, parent, kind)| TraceNode {
            id: id.to_string(),
            parent: parent.map(str::to_string),
            kind: kind.to_string(),
            data: Map::new(),
            metrics: BTreeMap::new(),
            path: Vec::new(),
        })
        .collect::<Vec<_>>();
        let index = validate_source_tree(&nodes).unwrap();
        let annotations = BTreeMap::from([
            (
                "s".to_string(),
                Annotation {
                    tag: "Execute".to_string(),
                    parent: None,
                    next: None,
                },
            ),
            (
                "p".to_string(),
                Annotation {
                    tag: "Fulfill request".to_string(),
                    parent: Some("s".to_string()),
                    next: None,
                },
            ),
            (
                "c1".to_string(),
                Annotation {
                    tag: "Inspect outer".to_string(),
                    parent: Some("p".to_string()),
                    next: Some("c4".to_string()),
                },
            ),
            (
                "c2".to_string(),
                Annotation {
                    tag: "Diagnose sibling".to_string(),
                    parent: Some("p".to_string()),
                    next: Some("c3".to_string()),
                },
            ),
        ]);
        let error = resolve_regions(&nodes, &index, &annotations)
            .unwrap_err()
            .to_string();
        assert!(error.contains("does not declare it as a semantic ancestor"));
    }

    #[test]
    fn noncontiguous_source_session_is_rejected_without_panicking() {
        let nodes = [
            ("s1", None, "session"),
            ("p1", Some("s1"), "prompt"),
            ("s2", None, "session"),
            ("p2", Some("s2"), "prompt"),
            ("c1", Some("p1"), "llm"),
        ]
        .into_iter()
        .map(|(id, parent, kind)| TraceNode {
            id: id.to_string(),
            parent: parent.map(str::to_string),
            kind: kind.to_string(),
            data: Map::new(),
            metrics: BTreeMap::new(),
            path: Vec::new(),
        })
        .collect::<Vec<_>>();
        let index = validate_source_tree(&nodes).unwrap();
        let annotations = BTreeMap::from([
            (
                "s1".to_string(),
                Annotation {
                    tag: "Run first".to_string(),
                    parent: None,
                    next: None,
                },
            ),
            (
                "p1".to_string(),
                Annotation {
                    tag: "Handle first".to_string(),
                    parent: Some("s1".to_string()),
                    next: None,
                },
            ),
            (
                "s2".to_string(),
                Annotation {
                    tag: "Run second".to_string(),
                    parent: None,
                    next: None,
                },
            ),
            (
                "p2".to_string(),
                Annotation {
                    tag: "Handle second".to_string(),
                    parent: Some("s2".to_string()),
                    next: None,
                },
            ),
        ]);
        let error = resolve_regions(&nodes, &index, &annotations)
            .unwrap_err()
            .to_string();
        assert!(error.contains("contiguous source-tree block"));
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
        let warnings = hierarchy_diagnostics(&nodes, &regions, ProfileView::Operations).warnings;
        assert!(
            warnings
                .iter()
                .any(|warning| warning.contains("flat fan-out"))
        );
    }

    #[test]
    fn near_name_distance_detects_small_lexical_variants() {
        assert_eq!(levenshtein_distance("configure", "reconfigure"), 2);
        assert_eq!(levenshtein_distance("test", "retest"), 2);
        assert!(levenshtein_distance("inspect", "validate") > 2);
    }

    #[test]
    fn near_name_candidates_are_exhaustive_and_unicode_uses_character_length() {
        let mut names = (0..30)
            .map(|index| format!("inspect {index:02}"))
            .collect::<Vec<_>>();
        names.extend(["界界".to_string(), "aa".to_string()]);
        let candidates = find_near_name_candidates(&names);
        assert!(candidates.len() > 25);
        assert!(candidates.iter().any(|candidate| {
            candidate.left == "inspect 28" && candidate.right == "inspect 29"
        }));
        assert!(
            candidates
                .iter()
                .any(|candidate| candidate.left == "界界" && candidate.right == "aa")
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

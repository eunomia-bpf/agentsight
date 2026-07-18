use base64::Engine as _;
use flate2::{Compression, write::GzEncoder};
use font8x8::{BASIC_FONTS, UnicodeFonts};
use serde::Serialize;
use serde::ser::{SerializeTuple, Serializer};
use std::collections::{BTreeMap, BTreeSet, HashMap, HashSet};
use std::f32::consts::PI;
use std::io::{Read, Write};
use std::path::{Path, PathBuf};
use std::process::{Child, ChildStdin, Command, Stdio};
use tiny_skia::{Color, FillRule, Paint, PathBuilder, Pixmap, Rect, Stroke, Transform};

pub(crate) const PLOT_WIDTH: u32 = 1200;
pub(crate) const PLOT_HEIGHT: u32 = 675;
pub(crate) const ARTIFACT_WIDTH: u32 = 1264;
pub(crate) const ARTIFACT_HEIGHT: u32 = 865;
const PLOT_LEFT: f32 = 32.0;
const PLOT_TOP: f32 = 104.0;
const MAX_FRAMES: usize = 360;
const FPS: u32 = 12;
const TRANSITION_FRAMES: usize = 6;
const DIRECTORY_MAX_SHARE: f32 = 0.42;
const DIRECTORY_COUNT_EXPONENT: f32 = 0.4;
const DIRECTORY_PSEUDOCOUNT: f32 = 8.0;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) enum ActionKind {
    Read,
    Write,
    Create,
    Rename,
    Delete,
}

impl ActionKind {
    fn label(self) -> &'static str {
        match self {
            Self::Read => "read",
            Self::Write => "write",
            Self::Create => "create",
            Self::Rename => "rename",
            Self::Delete => "delete",
        }
    }

    fn focus_code(self) -> u8 {
        match self {
            Self::Read => 1,
            Self::Write => 2,
            Self::Create => 3,
            Self::Rename => 4,
            Self::Delete => 5,
        }
    }

    fn lifecycle_code(self) -> u8 {
        match self {
            Self::Create => 1,
            Self::Rename => 2,
            Self::Delete => 3,
            _ => 0,
        }
    }

    fn importance_gain(self) -> f32 {
        match self {
            Self::Read => 1.0,
            Self::Write => 2.5,
            Self::Create | Self::Rename | Self::Delete => 4.0,
        }
    }
}

#[derive(Clone, Debug)]
pub(crate) struct FileAction {
    pub event_id: String,
    pub session_id: String,
    pub vendor: String,
    pub timestamp_ms: i64,
    pub kind: ActionKind,
    pub path: String,
    pub old_path: Option<String>,
}

#[derive(Clone, Debug)]
pub(crate) struct SceneInput {
    pub repository: String,
    pub revision: String,
    pub window_start_ms: i64,
    pub window_end_ms: i64,
    pub session_scope: String,
    pub session_count: usize,
    pub actions: Vec<FileAction>,
    pub commit_times: Vec<i64>,
}

#[derive(Clone, Serialize)]
pub(crate) struct SceneMeta {
    repository: String,
    revision: String,
    window_start_ms: i64,
    window_end_ms: i64,
    session_scope: String,
    session_count: usize,
    action_count: usize,
    frame_count: usize,
    fps: u32,
}

#[derive(Clone)]
pub(crate) struct StarVisual {
    id: u32,
    path_id: u32,
    x: f32,
    y: f32,
    diameter: f32,
    opacity: f32,
    color: [u8; 3],
    importance: f32,
    focus: u8,
    attention: f32,
    lifecycle: u8,
    lifecycle_progress: f32,
    visits: u32,
    sessions: u16,
}

impl Serialize for StarVisual {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        let mut tuple = serializer.serialize_tuple(14)?;
        tuple.serialize_element(&self.id)?;
        tuple.serialize_element(&self.path_id)?;
        tuple.serialize_element(&quantize_u16(self.x / PLOT_WIDTH as f32))?;
        tuple.serialize_element(&quantize_u16(self.y / PLOT_HEIGHT as f32))?;
        tuple.serialize_element(&quantize_u8(self.diameter / 12.0))?;
        tuple.serialize_element(&quantize_u8(self.opacity))?;
        tuple.serialize_element(&pack_color(self.color))?;
        tuple.serialize_element(&quantize_u8(self.importance))?;
        tuple.serialize_element(&self.focus)?;
        tuple.serialize_element(&quantize_u8(self.attention))?;
        tuple.serialize_element(&self.lifecycle)?;
        tuple.serialize_element(&quantize_u8(self.lifecycle_progress))?;
        tuple.serialize_element(&self.visits)?;
        tuple.serialize_element(&self.sessions)?;
        tuple.end()
    }
}

#[derive(Clone, Serialize)]
pub(crate) struct SceneFrame {
    #[serde(rename = "t")]
    timestamp_ms: i64,
    #[serde(rename = "c")]
    commit_flash: bool,
    #[serde(rename = "n")]
    summary: String,
    #[serde(rename = "s")]
    stars: Vec<StarVisual>,
}

#[derive(Clone, Serialize)]
pub(crate) struct SceneTimeline {
    meta: SceneMeta,
    paths: Vec<String>,
    frames: Vec<SceneFrame>,
}

impl SceneTimeline {
    pub(crate) fn frame_count(&self) -> usize {
        self.frames.len()
    }

    pub(crate) fn fps(&self) -> u32 {
        self.meta.fps
    }

    pub(crate) fn final_frame(&self) -> &SceneFrame {
        self.frames
            .last()
            .expect("timeline always contains a frame")
    }
}

#[derive(Clone)]
struct Node {
    id: u32,
    path_id: u32,
    path: String,
    top: String,
    local_x: f32,
    local_y: f32,
    velocity_x: f32,
    velocity_y: f32,
    visits: u32,
    sessions: HashSet<u32>,
    importance_raw: f32,
    importance_step: usize,
    importance: f32,
    base_diameter: f32,
    birth_frame: usize,
    delete_frame: Option<usize>,
    last_frame: usize,
    focus: ActionKind,
    lifecycle: u8,
    lifecycle_frame: Option<usize>,
    color_from: [u8; 3],
    color_to: [u8; 3],
    color_frame: usize,
}

#[derive(Clone)]
struct Cluster {
    x: f32,
    y: f32,
    home_x: f32,
    home_y: f32,
    velocity_x: f32,
    velocity_y: f32,
    radius: f32,
    share: f32,
    importance: f32,
}

struct Engine {
    repository: String,
    revision: String,
    nodes: BTreeMap<u32, Node>,
    path_index: HashMap<String, u32>,
    paths: Vec<String>,
    path_ids: HashMap<String, u32>,
    clusters: BTreeMap<String, Cluster>,
    top_hues: HashMap<String, f32>,
    next_node_id: u32,
    importance_half_life: f32,
}

#[derive(Clone)]
struct Profile {
    members: Vec<u32>,
    radius: f32,
}

impl Engine {
    fn new(input: &SceneInput, event_group_count: usize) -> Self {
        let mut tops = BTreeSet::new();
        for action in &input.actions {
            tops.insert(top_directory(&action.path));
            if let Some(old_path) = &action.old_path {
                tops.insert(top_directory(old_path));
            }
        }
        let seed = hash_unit(&format!("{}:{}", input.repository, input.revision)) * 360.0;
        let top_hues = tops
            .into_iter()
            .enumerate()
            .map(|(rank, top)| (top, (seed + 137.508 * rank as f32) % 360.0))
            .collect();
        Self {
            repository: input.repository.clone(),
            revision: input.revision.clone(),
            nodes: BTreeMap::new(),
            path_index: HashMap::new(),
            paths: Vec::new(),
            path_ids: HashMap::new(),
            clusters: BTreeMap::new(),
            top_hues,
            next_node_id: 0,
            importance_half_life: (event_group_count as f32 * 0.08).clamp(240.0, 2400.0),
        }
    }

    fn path_id(&mut self, path: &str) -> u32 {
        if let Some(id) = self.path_ids.get(path) {
            return *id;
        }
        let id = self.paths.len() as u32;
        self.paths.push(path.to_string());
        self.path_ids.insert(path.to_string(), id);
        id
    }

    fn ensure_cluster(&mut self, top: &str) {
        if self.clusters.contains_key(top) {
            return;
        }
        let rank = self.clusters.len();
        let angle = hash_unit(&format!("{}:{}", self.repository, self.revision)) * 2.0 * PI
            + rank as f32 * 2.399_963_1;
        let radius = if rank == 0 {
            0.0
        } else {
            (72.0 + 54.0 * (rank as f32).sqrt()).min(292.0)
        };
        let home_x = PLOT_WIDTH as f32 / 2.0 + 1.55 * radius * angle.cos();
        let home_y = PLOT_HEIGHT as f32 / 2.0 + 0.88 * radius * angle.sin();
        self.clusters.insert(
            top.to_string(),
            Cluster {
                x: home_x,
                y: home_y,
                home_x,
                home_y,
                velocity_x: 0.0,
                velocity_y: 0.0,
                radius: 42.0,
                share: 1.0,
                importance: 0.0,
            },
        );
    }

    fn color_for_path(&self, path: &str) -> [u8; 3] {
        let top = top_directory(path);
        let parent = parent_directory(path);
        let depth = directory_parts(path).len().saturating_sub(1) as f32;
        let hue = self.top_hues.get(&top).copied().unwrap_or(190.0)
            + (hash_unit(&parent) * 2.0 - 1.0) * 9.0;
        oklch_rgb(
            (0.58 + 0.055 * depth).clamp(0.58, 0.84),
            (0.17 - 0.015 * depth).clamp(0.08, 0.17),
            hue,
        )
    }

    fn birth_position(&self, path: &str, top: &str) -> (f32, f32) {
        let parent = parent_directory(path);
        let parts = directory_parts(path);
        let mut prefix_candidate = None;
        for node in self.nodes.values().rev() {
            if node.delete_frame.is_some() || node.top != top {
                continue;
            }
            if parent_directory(&node.path) == parent {
                return offset_near(node.local_x, node.local_y, path, 13.0);
            }
            let common = common_prefix_depth(&parts, &directory_parts(&node.path));
            if common > 0 && prefix_candidate.is_none() {
                prefix_candidate = Some((node.local_x, node.local_y));
            }
        }
        if let Some((x, y)) = prefix_candidate {
            return offset_near(x, y, path, 18.0);
        }
        let angle = hash_unit(&format!("{path}:birth")) * 2.0 * PI;
        (28.0 * angle.cos(), 28.0 * angle.sin())
    }

    fn create_node(&mut self, action: &FileAction, event_step: usize, frame: usize) -> u32 {
        if let Some(id) = self.path_index.get(&action.path) {
            return *id;
        }
        let top = top_directory(&action.path);
        self.ensure_cluster(&top);
        let (local_x, local_y) = self.birth_position(&action.path, &top);
        let color = self.color_for_path(&action.path);
        let path_id = self.path_id(&action.path);
        let id = self.next_node_id;
        self.next_node_id += 1;
        self.nodes.insert(
            id,
            Node {
                id,
                path_id,
                path: action.path.clone(),
                top,
                local_x,
                local_y,
                velocity_x: 0.0,
                velocity_y: 0.0,
                visits: 0,
                sessions: HashSet::new(),
                importance_raw: 0.0,
                importance_step: event_step,
                importance: 0.0,
                base_diameter: 6.0,
                birth_frame: frame,
                delete_frame: None,
                last_frame: frame,
                focus: action.kind,
                lifecycle: action.kind.lifecycle_code(),
                lifecycle_frame: (action.kind.lifecycle_code() != 0).then_some(frame),
                color_from: color,
                color_to: color,
                color_frame: frame,
            },
        );
        self.path_index.insert(action.path.clone(), id);
        id
    }

    fn apply_action(&mut self, action: &FileAction, event_step: usize, frame: usize) {
        let id = if action.kind == ActionKind::Rename {
            self.rename_node(action, event_step, frame)
        } else {
            self.create_node(action, event_step, frame)
        };
        let half_life = self.importance_half_life;
        let session_hash = hash32(&action.session_id);
        let node = self.nodes.get_mut(&id).expect("created node exists");
        let age = event_step.saturating_sub(node.importance_step) as f32;
        node.importance_raw *= 2.0_f32.powf(-age / half_life);
        node.importance_step = event_step;
        let mut gain = action.kind.importance_gain();
        if node.sessions.insert(session_hash) {
            gain += 1.5;
        }
        node.importance_raw += gain;
        node.visits += if action.kind == ActionKind::Read {
            1
        } else {
            2
        };
        node.last_frame = frame;
        node.focus = action.kind;
        node.delete_frame = (action.kind == ActionKind::Delete).then_some(frame);
        if action.kind.lifecycle_code() != 0 {
            node.lifecycle = action.kind.lifecycle_code();
            node.lifecycle_frame = Some(frame);
        }
    }

    fn rename_node(&mut self, action: &FileAction, event_step: usize, frame: usize) -> u32 {
        let old_id = action
            .old_path
            .as_ref()
            .and_then(|path| self.path_index.get(path))
            .copied();
        let Some(id) = old_id else {
            return self.create_node(action, event_step, frame);
        };
        let (old_top, old_x, old_y, old_color, old_path) = {
            let node = self.nodes.get(&id).expect("renamed node exists");
            let cluster = self.clusters.get(&node.top).expect("cluster exists");
            (
                node.top.clone(),
                cluster.x + node.local_x,
                cluster.y + node.local_y,
                current_node_color(node, frame),
                node.path.clone(),
            )
        };
        let new_top = top_directory(&action.path);
        self.ensure_cluster(&new_top);
        let new_center = self
            .clusters
            .get(&new_top)
            .expect("new cluster exists")
            .clone();
        let new_color = self.color_for_path(&action.path);
        let path_id = self.path_id(&action.path);
        self.path_index.remove(&old_path);
        let node = self.nodes.get_mut(&id).expect("renamed node exists");
        node.path = action.path.clone();
        node.path_id = path_id;
        node.top = new_top;
        node.local_x = old_x - new_center.x;
        node.local_y = old_y - new_center.y;
        node.color_from = old_color;
        node.color_to = new_color;
        node.color_frame = frame;
        node.delete_frame = None;
        self.path_index.insert(action.path.clone(), id);
        if old_top != node.top {
            node.velocity_x *= 0.4;
            node.velocity_y *= 0.4;
        }
        id
    }

    fn prune_deleted(&mut self, frame: usize) {
        let removed = self
            .nodes
            .iter()
            .filter_map(|(id, node)| {
                node.delete_frame
                    .filter(|deleted| frame.saturating_sub(*deleted) >= TRANSITION_FRAMES)
                    .map(|_| (*id, node.path.clone()))
            })
            .collect::<Vec<_>>();
        for (id, path) in removed {
            self.nodes.remove(&id);
            self.path_index.remove(&path);
        }
    }

    fn refresh_profiles(&mut self, event_step: usize, frame: usize) -> BTreeMap<String, Profile> {
        let active = self
            .nodes
            .iter()
            .filter(|(_, node)| node_opacity(node, frame) > 0.001)
            .map(|(id, _)| *id)
            .collect::<Vec<_>>();
        for id in &active {
            let node = self.nodes.get_mut(id).expect("active node exists");
            let age = event_step.saturating_sub(node.importance_step) as f32;
            node.importance_raw *= 2.0_f32.powf(-age / self.importance_half_life);
            node.importance_step = event_step;
        }
        let mut ranked = active
            .iter()
            .map(|id| self.nodes[id].importance_raw)
            .collect::<Vec<_>>();
        ranked.sort_by(f32::total_cmp);
        let p95 = ranked
            .get(((ranked.len().saturating_sub(1)) as f32 * 0.95) as usize)
            .copied()
            .unwrap_or(1.0)
            .max(1.0);
        for id in &active {
            let node = self.nodes.get_mut(id).expect("active node exists");
            node.importance = (node.importance_raw.ln_1p() / p95.ln_1p()).clamp(0.0, 1.0);
        }
        let mut groups: BTreeMap<String, Vec<u32>> = BTreeMap::new();
        for id in &active {
            groups
                .entry(self.nodes[id].top.clone())
                .or_default()
                .push(*id);
        }
        let rows = groups
            .iter()
            .map(|(top, members)| {
                let mean = members
                    .iter()
                    .map(|id| self.nodes[id].importance)
                    .sum::<f32>()
                    / members.len() as f32;
                let peak = members
                    .iter()
                    .map(|id| self.nodes[id].importance)
                    .fold(0.0, f32::max);
                let weight = (members.len() as f32 + DIRECTORY_PSEUDOCOUNT)
                    .powf(DIRECTORY_COUNT_EXPONENT)
                    * (0.8 + 0.2 * mean);
                (top.clone(), members.clone(), mean, peak, weight)
            })
            .collect::<Vec<_>>();
        let shares = capped_shares(&rows);
        let total = active.len().max(1) as f32;
        let resting = (6.0 * (480.0 / total.max(480.0)).sqrt()).clamp(0.85, 6.0);
        let mut profiles = BTreeMap::new();
        for (top, members, mean, peak, _) in rows {
            self.ensure_cluster(&top);
            let share = shares.get(&top).copied().unwrap_or(1.0);
            let cell_scale = (share * total / members.len() as f32)
                .sqrt()
                .clamp(0.52, 1.8);
            let importance = 0.7 * mean + 0.3 * peak;
            let radius = (0.34 * (share * PLOT_WIDTH as f32 * PLOT_HEIGHT as f32 / PI).sqrt())
                .clamp(24.0, 140.0);
            if let Some(cluster) = self.clusters.get_mut(&top) {
                cluster.share = share;
                cluster.radius += (radius - cluster.radius) * 0.18;
                cluster.importance = importance;
            }
            for id in &members {
                let node = self.nodes.get_mut(id).expect("profile node exists");
                node.base_diameter =
                    (resting * cell_scale * (0.62 + 0.38 * node.importance.sqrt()))
                        .clamp(0.85, 6.0);
            }
            profiles.insert(top, Profile { members, radius });
        }
        profiles
    }

    fn run_layout(&mut self, event_step: usize, frame: usize) {
        let profiles = self.refresh_profiles(event_step, frame);
        let node_count = profiles
            .values()
            .map(|profile| profile.members.len())
            .sum::<usize>();
        if node_count == 0 {
            return;
        }
        let microsteps = if node_count > 2_000 {
            2
        } else if node_count > 600 {
            3
        } else {
            4
        };
        for _ in 0..microsteps {
            self.step_clusters(&profiles);
            self.step_nodes(&profiles);
        }
    }

    fn step_clusters(&mut self, profiles: &BTreeMap<String, Profile>) {
        let keys = profiles.keys().cloned().collect::<Vec<_>>();
        let mut impulses: HashMap<String, (f32, f32)> = HashMap::new();
        for left in 0..keys.len() {
            for right in (left + 1)..keys.len() {
                let a = &self.clusters[&keys[left]];
                let b = &self.clusters[&keys[right]];
                let mut dx = b.x - a.x;
                let mut dy = b.y - a.y;
                let mut distance = dx.hypot(dy);
                if distance < 0.01 {
                    let angle = hash_unit(&format!("{}:{}", keys[left], keys[right])) * 2.0 * PI;
                    dx = angle.cos();
                    dy = angle.sin();
                    distance = 1.0;
                }
                let minimum = 0.78 * (a.radius + b.radius) + 12.0;
                let overlap = (minimum - distance).max(0.0);
                let soft = 110.0 / (distance + 30.0);
                let impulse = (0.015 * overlap + 0.006 * soft).min(1.8);
                let nx = dx / distance;
                let ny = dy / distance;
                let total = (a.share + b.share).max(0.001);
                add_impulse(
                    &mut impulses,
                    &keys[left],
                    -nx * impulse * b.share / total,
                    -ny * impulse * b.share / total,
                );
                add_impulse(
                    &mut impulses,
                    &keys[right],
                    nx * impulse * a.share / total,
                    ny * impulse * a.share / total,
                );
            }
        }
        for key in keys {
            let cluster = self.clusters.get_mut(&key).expect("cluster exists");
            let (ix, iy) = impulses.get(&key).copied().unwrap_or_default();
            let center_weight = (0.08 + 0.68 * cluster.importance).clamp(0.08, 0.76);
            let target_x =
                cluster.home_x * (1.0 - center_weight) + PLOT_WIDTH as f32 / 2.0 * center_weight;
            let target_y =
                cluster.home_y * (1.0 - center_weight) + PLOT_HEIGHT as f32 / 2.0 * center_weight;
            cluster.velocity_x += ix + (target_x - cluster.x) * 0.005;
            cluster.velocity_y += iy + (target_y - cluster.y) * 0.005;
            cluster.velocity_x = (cluster.velocity_x * 0.78).clamp(-3.0, 3.0);
            cluster.velocity_y = (cluster.velocity_y * 0.78).clamp(-3.0, 3.0);
            cluster.x = (cluster.x + cluster.velocity_x)
                .clamp(cluster.radius, PLOT_WIDTH as f32 - cluster.radius);
            cluster.y = (cluster.y + cluster.velocity_y)
                .clamp(cluster.radius, PLOT_HEIGHT as f32 - cluster.radius);
        }
    }

    fn step_nodes(&mut self, profiles: &BTreeMap<String, Profile>) {
        let mut forces: HashMap<u32, (f32, f32)> = HashMap::new();
        let mut parent_centroids: HashMap<(String, String), (f32, f32, usize)> = HashMap::new();
        let mut layout_centroids: HashMap<(String, String), (f32, f32, usize)> = HashMap::new();
        for (top, profile) in profiles {
            for id in &profile.members {
                let node = &self.nodes[id];
                add_centroid(
                    &mut parent_centroids,
                    (top.clone(), parent_directory(&node.path)),
                    node.local_x,
                    node.local_y,
                );
                add_centroid(
                    &mut layout_centroids,
                    (top.clone(), layout_directory(&node.path)),
                    node.local_x,
                    node.local_y,
                );
            }
        }
        for (top, profile) in profiles {
            for id in &profile.members {
                let node = &self.nodes[id];
                let parent = centroid(
                    &parent_centroids,
                    &(top.clone(), parent_directory(&node.path)),
                );
                let layout = centroid(
                    &layout_centroids,
                    &(top.clone(), layout_directory(&node.path)),
                );
                let mut force_x =
                    (parent.0 - node.local_x) * 0.015 + (layout.0 - node.local_x) * 0.005;
                let mut force_y =
                    (parent.1 - node.local_y) * 0.015 + (layout.1 - node.local_y) * 0.005;
                let center_pull = 0.0012 + 0.011 * node.importance;
                force_x -= node.local_x * center_pull;
                force_y -= node.local_y * center_pull;
                let distance = node.local_x.hypot(node.local_y);
                let envelope =
                    profile.radius * (0.75 + 0.2 * hash_unit(&format!("{}:envelope", node.path)));
                if distance > envelope && distance > 0.001 {
                    let pull = (distance - envelope) / distance * 0.035;
                    force_x -= node.local_x * pull;
                    force_y -= node.local_y * pull;
                }
                forces.insert(*id, (force_x, force_y));
            }
        }
        let cell_size = 10.0;
        let mut grids: HashMap<(String, i32, i32), Vec<u32>> = HashMap::new();
        for (top, profile) in profiles {
            for id in &profile.members {
                let node = &self.nodes[id];
                grids
                    .entry((
                        top.clone(),
                        (node.local_x / cell_size).floor() as i32,
                        (node.local_y / cell_size).floor() as i32,
                    ))
                    .or_default()
                    .push(*id);
            }
        }
        for (top, profile) in profiles {
            for id in &profile.members {
                let node = &self.nodes[id];
                let gx = (node.local_x / cell_size).floor() as i32;
                let gy = (node.local_y / cell_size).floor() as i32;
                for ox in -1..=1 {
                    for oy in -1..=1 {
                        for other_id in grids
                            .get(&(top.clone(), gx + ox, gy + oy))
                            .into_iter()
                            .flatten()
                        {
                            if other_id <= id {
                                continue;
                            }
                            let other = &self.nodes[other_id];
                            let mut dx = other.local_x - node.local_x;
                            let mut dy = other.local_y - node.local_y;
                            let mut distance = dx.hypot(dy);
                            if distance < 0.001 {
                                let angle = hash_unit(&format!("{}:{}", id, other_id)) * 2.0 * PI;
                                dx = angle.cos();
                                dy = angle.sin();
                                distance = 1.0;
                            }
                            let minimum = (node.base_diameter + other.base_diameter) * 0.5 + 1.2;
                            if distance >= minimum {
                                continue;
                            }
                            let impulse = ((minimum - distance) * 0.09).min(0.8);
                            let fx = dx / distance * impulse;
                            let fy = dy / distance * impulse;
                            add_force(&mut forces, *id, -fx, -fy);
                            add_force(&mut forces, *other_id, fx, fy);
                        }
                    }
                }
            }
        }
        for (id, (force_x, force_y)) in forces {
            let node = self.nodes.get_mut(&id).expect("force node exists");
            node.velocity_x = (node.velocity_x + force_x)
                .mul_add(0.72, 0.0)
                .clamp(-2.4, 2.4);
            node.velocity_y = (node.velocity_y + force_y)
                .mul_add(0.72, 0.0)
                .clamp(-2.4, 2.4);
            node.local_x += node.velocity_x;
            node.local_y += node.velocity_y;
        }
    }

    fn snapshot(
        &self,
        timestamp_ms: i64,
        frame: usize,
        commit_flash: bool,
        summary: String,
    ) -> SceneFrame {
        let mut stars = Vec::new();
        for node in self.nodes.values() {
            let opacity = node_opacity(node, frame);
            if opacity <= 0.001 {
                continue;
            }
            let cluster = self.clusters.get(&node.top).expect("node cluster exists");
            let age = frame.saturating_sub(node.last_frame) as f32;
            let attention = focus_strength(node.focus) * 2.0_f32.powf(-age / 1.35);
            let attention = if attention < 0.045 { 0.0 } else { attention };
            let diameter =
                node.base_diameter + (10.5 - node.base_diameter) * attention.clamp(0.0, 1.0);
            let lifecycle_progress = node
                .lifecycle_frame
                .map(|started| frame.saturating_sub(started) as f32 / TRANSITION_FRAMES as f32)
                .filter(|progress| *progress <= 1.0)
                .unwrap_or(1.0);
            let baseline = (0.22
                + 0.58 * node.importance.sqrt()
                + 0.08 / (1.0 + 0.18 * directory_parts(&node.path).len() as f32))
                .clamp(0.24, 0.9);
            stars.push(StarVisual {
                id: node.id,
                path_id: node.path_id,
                x: (cluster.x + node.local_x).clamp(2.0, PLOT_WIDTH as f32 - 2.0),
                y: (cluster.y + node.local_y).clamp(2.0, PLOT_HEIGHT as f32 - 2.0),
                diameter,
                opacity: baseline * opacity,
                color: current_node_color(node, frame),
                importance: node.importance,
                focus: node.focus.focus_code(),
                attention,
                lifecycle: if lifecycle_progress < 1.0 {
                    node.lifecycle
                } else {
                    0
                },
                lifecycle_progress,
                visits: node.visits,
                sessions: node.sessions.len().min(u16::MAX as usize) as u16,
            });
        }
        SceneFrame {
            timestamp_ms,
            commit_flash,
            summary,
            stars,
        }
    }
}

pub(crate) fn build_timeline(mut input: SceneInput) -> SceneTimeline {
    input.actions.sort_by(|left, right| {
        left.timestamp_ms
            .cmp(&right.timestamp_ms)
            .then_with(|| left.event_id.cmp(&right.event_id))
            .then_with(|| action_priority(left.kind).cmp(&action_priority(right.kind)))
            .then_with(|| left.path.cmp(&right.path))
    });
    input.commit_times.sort_unstable();
    let event_group_count = input
        .actions
        .iter()
        .map(|action| &action.event_id)
        .collect::<BTreeSet<_>>()
        .len();
    let action_count = input.actions.len();
    let mut engine = Engine::new(&input, event_group_count);
    let mut groups: Vec<Vec<FileAction>> = Vec::new();
    for action in std::mem::take(&mut input.actions) {
        if groups
            .last()
            .is_some_and(|group| group[0].event_id == action.event_id)
        {
            groups.last_mut().expect("last group exists").push(action);
        } else {
            groups.push(vec![action]);
        }
    }
    let action_frame_count = groups.len().min(MAX_FRAMES.saturating_sub(1));
    let mut buckets = vec![Vec::new(); action_frame_count];
    if action_frame_count > 0 {
        let group_count = groups.len();
        for (event_step, mut group) in groups.into_iter().enumerate() {
            let bucket =
                (event_step * action_frame_count / group_count).min(action_frame_count - 1);
            for action in &mut group {
                action.event_id = format!("{}\0{event_step}", action.event_id);
            }
            buckets[bucket].extend(group);
        }
    }
    let mut frames = vec![SceneFrame {
        timestamp_ms: input.window_start_ms,
        commit_flash: false,
        summary: "repository begins empty; stars appear on observed file actions".to_string(),
        stars: Vec::new(),
    }];
    let mut previous_timestamp = input.window_start_ms;
    for (bucket_index, bucket) in buckets.iter().enumerate() {
        let frame = bucket_index + 1;
        engine.prune_deleted(frame);
        let mut event_step = 0;
        for action in bucket {
            event_step = action
                .event_id
                .rsplit_once('\0')
                .and_then(|(_, value)| value.parse::<usize>().ok())
                .unwrap_or(event_step);
            engine.apply_action(action, event_step, frame);
        }
        engine.run_layout(event_step, frame);
        let timestamp = bucket
            .last()
            .map_or(previous_timestamp, |action| action.timestamp_ms);
        let commit_flash = input
            .commit_times
            .iter()
            .any(|commit| *commit > previous_timestamp && *commit <= timestamp);
        frames.push(engine.snapshot(timestamp, frame, commit_flash, summarize_actions(bucket)));
        previous_timestamp = timestamp;
    }
    let meta = SceneMeta {
        repository: input.repository,
        revision: input.revision,
        window_start_ms: input.window_start_ms,
        window_end_ms: input.window_end_ms,
        session_scope: input.session_scope,
        session_count: input.session_count,
        action_count,
        frame_count: frames.len(),
        fps: FPS,
    };
    SceneTimeline {
        meta,
        paths: engine.paths,
        frames,
    }
}

pub(crate) fn html_document(
    timeline: &SceneTimeline,
) -> Result<String, Box<dyn std::error::Error + Send + Sync>> {
    let json = serde_json::to_vec(timeline)?;
    let mut encoder = GzEncoder::new(Vec::new(), Compression::new(6));
    encoder.write_all(&json)?;
    let payload = base64::engine::general_purpose::STANDARD.encode(encoder.finish()?);
    Ok(format!(
        r#"<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="generator" content="agentsight-vis 0.2"><title>Repository Nebula · AgentSight</title><style>
:root{{color-scheme:dark;font-family:Inter,ui-sans-serif,system-ui,sans-serif;background:#070b12;color:#dce8f7}}*{{box-sizing:border-box}}body{{margin:0;background:#070b12}}.artifact{{width:1264px;padding:24px 32px 18px;background:#070b12;transition:box-shadow .12s}}.artifact.commit{{box-shadow:inset 0 0 0 2px #efd265,0 0 30px rgba(239,210,101,.4)}}header{{height:66px;border-bottom:1px solid rgba(135,160,190,.18)}}.eyebrow,.mode{{font:10px ui-monospace,monospace;letter-spacing:.12em;text-transform:uppercase}}.eyebrow{{color:#61d7bf}}h1{{font-size:24px;margin:5px 0 2px}}p{{font-size:11px;color:#71839a;margin:0}}canvas{{display:block;width:1200px;height:675px}}.timeline{{display:grid;grid-template-columns:42px 1fr 190px;gap:12px;align-items:center;border-top:1px solid rgba(135,160,190,.18);padding:12px 0 7px}}button{{width:36px;height:36px;border-radius:50%;border:1px solid rgba(97,215,191,.4);background:#10231f;color:#61d7bf}}input{{width:100%;accent-color:#61d7bf}}output,footer{{font:9px ui-monospace,monospace;color:#8798ad}}output{{text-align:right}}.legend{{display:flex;gap:18px;font:9px ui-monospace,monospace;color:#71839a}}.legend i{{display:inline-block;width:13px;height:3px;margin-right:5px;vertical-align:middle}}footer{{margin-top:8px}}.tip{{position:fixed;display:none;pointer-events:none;white-space:pre;padding:8px 10px;border:1px solid #304153;background:#0a111c;color:#dce8f7;font:10px ui-monospace,monospace;border-radius:6px;z-index:4}}
</style></head><body><main id="artifact" class="artifact"><header><span class="eyebrow">AgentSight · repository evolution</span><h1>Repository Nebula</h1><p>Files are stars. Directories are color and path attraction, never nodes.</p></header><canvas id="chart" width="1200" height="675"></canvas><section class="timeline"><button id="play">▶</button><input id="timeline" type="range" min="0" max="0" step="1"><output id="label"></output></section><section class="legend"><span><i style="background:#f7ffff"></i>read attention</span><span><i style="background:#ff9678"></i>write ripple</span><span><i style="background:#75f0a9"></i>create</span><span><i style="background:#63dfff"></i>rename</span><span><i style="background:#ff647c"></i>delete</span><span><i style="background:#efd265"></i>commit frame</span></section><footer id="footer"></footer></main><div id="tip" class="tip"></div><script>
const P='{payload}';(async()=>{{const bytes=Uint8Array.from(atob(P),c=>c.charCodeAt(0)),stream=new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip')),D=JSON.parse(await new Response(stream).text());const C=document.querySelector('#chart'),X=C.getContext('2d'),R=document.querySelector('#timeline'),L=document.querySelector('#label'),A=document.querySelector('#artifact'),T=document.querySelector('#tip');let current=0,raf=0;R.max=String(D.frames.length-1);
const rgb=n=>`rgb(${{n>>16&255}} ${{n>>8&255}} ${{n&255}})`;const rgba=(n,a)=>`rgba(${{n>>16&255}},${{n>>8&255}},${{n&255}},${{a}})`;const val=(s,i)=>i===2||i===3?s[i]/65535:i===4?s[i]/255*12:i===5||i===7||i===9||i===11?s[i]/255:s[i];
function stars(frame){{return frame.s.map(s=>({{id:s[0],path:s[1],x:val(s,2)*1200,y:val(s,3)*675,d:val(s,4),o:val(s,5),color:s[6],imp:val(s,7),focus:s[8],attention:val(s,9),life:s[10],progress:val(s,11),visits:s[12],sessions:s[13]}}))}}
function circle(x,y,r,fill,alpha=1){{X.globalAlpha=alpha;X.fillStyle=fill;X.beginPath();X.arc(x,y,Math.max(.1,r),0,Math.PI*2);X.fill()}}function ring(x,y,r,color,alpha,w=1.2){{X.globalAlpha=alpha;X.strokeStyle=color;X.lineWidth=w;X.beginPath();X.arc(x,y,Math.max(.1,r),0,Math.PI*2);X.stroke()}}
function draw(index,next=index,mix=0){{const f=D.frames[index],a=stars(f),b=new Map(stars(D.frames[next]).map(s=>[s.id,s]));X.globalAlpha=1;X.fillStyle='#070b12';X.fillRect(0,0,1200,675);const rows=a.map(s=>{{const n=b.get(s.id);return n?{{...s,x:s.x+(n.x-s.x)*mix,y:s.y+(n.y-s.y)*mix,d:s.d+(n.d-s.d)*mix,o:s.o+(n.o-s.o)*mix,attention:s.attention+(n.attention-s.attention)*mix}}:{{...s,o:s.o*(1-mix)}}}});rows.filter(s=>s.attention>0).sort((x,y)=>y.attention-x.attention).slice(0,4).forEach(s=>{{circle(s.x,s.y,s.d*.8+7,rgba(0xf7ffff,.08+.16*s.attention));ring(s.x,s.y,s.d*.5+4,'#f7ffff',.1+.5*s.attention)}});rows.forEach(s=>{{if(s.attention>0)circle(s.x,s.y,s.d*.55+8,rgb(s.color),.04+.13*s.attention);circle(s.x,s.y,s.d/2,rgb(s.color),s.o)}});rows.filter(s=>s.focus===2&&s.attention>0).sort((x,y)=>y.attention-x.attention).slice(0,12).forEach(s=>{{const p=1-s.attention;ring(s.x,s.y,s.d/2+8+28*p,'#ff9678',.6*(1-p))}});rows.filter(s=>s.life>0&&s.progress<1).sort((x,y)=>x.progress-y.progress).slice(0,12).forEach(s=>{{const color=['','#75f0a9','#63dfff','#ff647c'][s.life];ring(s.x,s.y,s.d/2+10+24*s.progress,color,.85*(1-s.progress),1.4)}});X.globalAlpha=1;X.fillStyle='rgba(5,10,18,.78)';X.fillRect(10,10,620,30);X.fillStyle='#dce8f7';X.font='12px ui-monospace,monospace';X.fillText(f.n,20,29,600);current=index;R.value=String(index);L.textContent=`${{new Date(f.t).toISOString()}} · ${{index+1}}/${{D.frames.length}} · ${{a.length}} files`;A.classList.toggle('commit',f.c);window.__AGENTSIGHT_READY__=true;window.__AGENTSIGHT_FRAME__=index;return rows}}
let visible=[];function render(i){{visible=draw(i);}}function stop(){{cancelAnimationFrame(raf);raf=0;document.querySelector('#play').textContent='▶'}}document.querySelector('#play').onclick=()=>{{if(raf)return stop();const start=performance.now(),from=current,duration=Math.max(1000,(D.frames.length-from)/D.meta.fps*1000);document.querySelector('#play').textContent='Ⅱ';const tick=now=>{{const p=Math.min(1,(now-start)/duration),exact=from+p*(D.frames.length-1-from),i=Math.min(D.frames.length-1,Math.floor(exact)),n=Math.min(D.frames.length-1,i+1);visible=draw(i,n,exact-i);if(p<1)raf=requestAnimationFrame(tick);else stop()}};raf=requestAnimationFrame(tick)}};R.oninput=()=>{{stop();render(Number(R.value))}};C.onmousemove=e=>{{const box=C.getBoundingClientRect(),x=(e.clientX-box.left)*1200/box.width,y=(e.clientY-box.top)*675/box.height;let hit=null,best=100;for(const s of visible){{const d=Math.hypot(s.x-x,s.y-y);if(d<Math.max(5,s.d)&&d<best){{hit=s;best=d}}}}if(!hit){{T.style.display='none';return}}T.textContent=`${{D.paths[hit.path]}}\n${{hit.visits}} file actions · ${{hit.sessions}} sessions\nimportance ${{Math.round(hit.imp*100)}}%`;T.style.display='block';T.style.left=`${{e.clientX+14}}px`;T.style.top=`${{e.clientY+14}}px`}};C.onmouseleave=()=>T.style.display='none';document.querySelector('#footer').textContent=`repository: ${{D.meta.repository}} · scope: ${{D.meta.session_scope}} · revision: ${{D.meta.revision.slice(0,12)}} · ${{D.meta.session_count}} sessions · ${{D.meta.action_count}} file actions`;render(0)}})().catch(error=>{{document.body.textContent=`AgentSight visualization failed: ${{error.message}}`}});
</script></body></html>"#,
        payload = payload
    ))
}

pub(crate) fn render_pixmap(
    timeline: &SceneTimeline,
    frame: &SceneFrame,
    frame_index: usize,
) -> Pixmap {
    let mut pixmap = Pixmap::new(ARTIFACT_WIDTH, ARTIFACT_HEIGHT).expect("valid artifact size");
    pixmap.fill(Color::from_rgba8(7, 11, 18, 255));
    fill_rect(&mut pixmap, 32.0, 89.0, 1200.0, 1.0, [62, 78, 98, 90]);
    draw_text(
        &mut pixmap,
        32,
        24,
        "AGENTSIGHT / REPOSITORY EVOLUTION",
        1,
        [97, 215, 191, 255],
    );
    draw_text(
        &mut pixmap,
        32,
        43,
        "REPOSITORY NEBULA",
        2,
        [220, 232, 247, 255],
    );
    draw_text(
        &mut pixmap,
        32,
        70,
        "FILES ARE STARS; DIRECTORIES ARE COLOR AND PATH ATTRACTION",
        1,
        [113, 131, 154, 255],
    );
    fill_rect(
        &mut pixmap,
        PLOT_LEFT + 10.0,
        PLOT_TOP + 10.0,
        620.0,
        26.0,
        [5, 10, 18, 205],
    );
    draw_text(
        &mut pixmap,
        (PLOT_LEFT + 20.0) as i32,
        (PLOT_TOP + 19.0) as i32,
        &truncate_chars(&ascii_upper(&frame.summary), 67),
        1,
        [220, 232, 247, 255],
    );
    let mut reads = frame
        .stars
        .iter()
        .filter(|star| star.focus == 1 && star.attention > 0.0)
        .collect::<Vec<_>>();
    reads.sort_by(|left, right| right.attention.total_cmp(&left.attention));
    for star in reads.into_iter().take(4) {
        let x = PLOT_LEFT + star.x;
        let y = PLOT_TOP + star.y;
        fill_circle(
            &mut pixmap,
            x,
            y,
            star.diameter * 0.8 + 7.0,
            [247, 255, 255, (18.0 + 42.0 * star.attention) as u8],
        );
        stroke_circle(
            &mut pixmap,
            x,
            y,
            star.diameter * 0.5 + 4.0,
            [247, 255, 255, (30.0 + 125.0 * star.attention) as u8],
            1.2,
        );
    }
    for star in &frame.stars {
        let x = PLOT_LEFT + star.x;
        let y = PLOT_TOP + star.y;
        if star.attention > 0.0 {
            fill_circle(
                &mut pixmap,
                x,
                y,
                star.diameter * 0.55 + 8.0,
                [
                    star.color[0],
                    star.color[1],
                    star.color[2],
                    (10.0 + 33.0 * star.attention) as u8,
                ],
            );
        }
        fill_circle(
            &mut pixmap,
            x,
            y,
            star.diameter * 0.5,
            [
                star.color[0],
                star.color[1],
                star.color[2],
                (255.0 * star.opacity) as u8,
            ],
        );
    }
    let mut writes = frame
        .stars
        .iter()
        .filter(|star| star.focus == 2 && star.attention > 0.0)
        .collect::<Vec<_>>();
    writes.sort_by(|left, right| right.attention.total_cmp(&left.attention));
    for star in writes.into_iter().take(12) {
        let x = PLOT_LEFT + star.x;
        let y = PLOT_TOP + star.y;
        let progress = 1.0 - star.attention;
        stroke_circle(
            &mut pixmap,
            x,
            y,
            star.diameter * 0.5 + 8.0 + 28.0 * progress,
            [255, 150, 120, (150.0 * (1.0 - progress)) as u8],
            1.25,
        );
    }
    let mut lifecycle = frame
        .stars
        .iter()
        .filter(|star| star.lifecycle > 0 && star.lifecycle_progress < 1.0)
        .collect::<Vec<_>>();
    lifecycle.sort_by(|left, right| left.lifecycle_progress.total_cmp(&right.lifecycle_progress));
    for star in lifecycle.into_iter().take(12) {
        let x = PLOT_LEFT + star.x;
        let y = PLOT_TOP + star.y;
        let color = match star.lifecycle {
            1 => [117, 240, 169],
            2 => [99, 223, 255],
            _ => [255, 100, 124],
        };
        stroke_circle(
            &mut pixmap,
            x,
            y,
            star.diameter * 0.5 + 10.0 + 24.0 * star.lifecycle_progress,
            [
                color[0],
                color[1],
                color[2],
                (220.0 * (1.0 - star.lifecycle_progress)) as u8,
            ],
            1.4,
        );
    }
    let progress = if timeline.frames.len() <= 1 {
        1.0
    } else {
        frame_index as f32 / (timeline.frames.len() - 1) as f32
    };
    fill_rect(&mut pixmap, 32.0, 791.0, 1200.0, 1.0, [62, 78, 98, 110]);
    fill_rect(&mut pixmap, 72.0, 812.0, 1050.0, 2.0, [36, 54, 70, 255]);
    fill_rect(
        &mut pixmap,
        72.0,
        812.0,
        1050.0 * progress,
        2.0,
        [97, 215, 191, 255],
    );
    fill_circle(
        &mut pixmap,
        72.0 + 1050.0 * progress,
        813.0,
        4.0,
        [97, 215, 191, 255],
    );
    let label = format!(
        "{}  FRAME {}/{}  {} FILES",
        iso_label(frame.timestamp_ms),
        frame_index + 1,
        timeline.frames.len(),
        frame.stars.len()
    );
    draw_text(&mut pixmap, 32, 829, &label, 1, [139, 157, 179, 255]);
    let footer = format!(
        "{} / {} SESSIONS / {} FILE ACTIONS",
        ascii_upper(&timeline.meta.repository),
        timeline.meta.session_count,
        timeline.meta.action_count
    );
    draw_text(&mut pixmap, 690, 829, &footer, 1, [102, 120, 142, 255]);
    if frame.commit_flash {
        stroke_rect(
            &mut pixmap,
            1.5,
            1.5,
            ARTIFACT_WIDTH as f32 - 3.0,
            ARTIFACT_HEIGHT as f32 - 3.0,
            [239, 210, 101, 235],
            2.0,
        );
    }
    pixmap
}

pub(crate) fn svg_document(timeline: &SceneTimeline) -> String {
    let frame = timeline.final_frame();
    let index = timeline.frames.len() - 1;
    let mut svg = format!(
        r##"<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{ARTIFACT_WIDTH}" height="{ARTIFACT_HEIGHT}" viewBox="0 0 {ARTIFACT_WIDTH} {ARTIFACT_HEIGHT}"><metadata>{{"generator":"agentsight-vis 0.2","repository":"{}","revision":"{}","frame":{index}}}</metadata><rect width="100%" height="100%" fill="#070b12"/><text x="32" y="32" fill="#61d7bf" font-family="ui-monospace,monospace" font-size="10" letter-spacing="1.2">AGENTSIGHT · REPOSITORY EVOLUTION</text><text x="32" y="59" fill="#dce8f7" font-family="ui-sans-serif,system-ui" font-size="24" font-weight="600">Repository Nebula</text><text x="32" y="78" fill="#71839a" font-family="ui-monospace,monospace" font-size="10">Files are stars. Directories are color and path attraction, never nodes.</text><line x1="32" y1="89" x2="1232" y2="89" stroke="#273343"/>"##,
        escape_xml(&timeline.meta.repository),
        escape_xml(&timeline.meta.revision)
    );
    svg.push_str(&format!("<rect x=\"42\" y=\"114\" width=\"620\" height=\"26\" rx=\"5\" fill=\"#050a12\" opacity=\".8\"/><text x=\"52\" y=\"132\" fill=\"#dce8f7\" font-family=\"ui-monospace,monospace\" font-size=\"11\">{}</text>", escape_xml(&truncate_chars(&frame.summary, 85))));
    let mut reads = frame
        .stars
        .iter()
        .filter(|star| star.focus == 1 && star.attention > 0.0)
        .collect::<Vec<_>>();
    reads.sort_by(|left, right| right.attention.total_cmp(&left.attention));
    for star in reads.into_iter().take(4) {
        let x = PLOT_LEFT + star.x;
        let y = PLOT_TOP + star.y;
        svg.push_str(&format!("<circle cx=\"{x:.2}\" cy=\"{y:.2}\" r=\"{:.2}\" fill=\"#f7ffff\" opacity=\"{:.3}\"/><circle cx=\"{x:.2}\" cy=\"{y:.2}\" r=\"{:.2}\" fill=\"none\" stroke=\"#f7ffff\" stroke-width=\"1.2\" opacity=\"{:.3}\"/>", star.diameter * 0.8 + 7.0, 0.07 + 0.16 * star.attention, star.diameter * 0.5 + 4.0, 0.12 + 0.49 * star.attention));
    }
    for star in &frame.stars {
        let x = PLOT_LEFT + star.x;
        let y = PLOT_TOP + star.y;
        let color = format!(
            "#{:02x}{:02x}{:02x}",
            star.color[0], star.color[1], star.color[2]
        );
        if star.attention > 0.0 {
            svg.push_str(&format!("<circle cx=\"{x:.2}\" cy=\"{y:.2}\" r=\"{:.2}\" fill=\"{color}\" opacity=\"{:.3}\"/>", star.diameter * 0.55 + 8.0, 0.04 + 0.13 * star.attention));
        }
        svg.push_str(&format!("<circle cx=\"{x:.2}\" cy=\"{y:.2}\" r=\"{:.2}\" fill=\"{color}\" opacity=\"{:.3}\"><title>{}</title></circle>", star.diameter * 0.5, star.opacity, escape_xml(&timeline.paths[star.path_id as usize])));
    }
    let mut writes = frame
        .stars
        .iter()
        .filter(|star| star.focus == 2 && star.attention > 0.0)
        .collect::<Vec<_>>();
    writes.sort_by(|left, right| right.attention.total_cmp(&left.attention));
    for star in writes.into_iter().take(12) {
        let x = PLOT_LEFT + star.x;
        let y = PLOT_TOP + star.y;
        let progress = 1.0 - star.attention;
        svg.push_str(&format!("<circle cx=\"{x:.2}\" cy=\"{y:.2}\" r=\"{:.2}\" fill=\"none\" stroke=\"#ff9678\" stroke-width=\"1.25\" opacity=\"{:.3}\"/>", star.diameter * 0.5 + 8.0 + 28.0 * progress, 0.59 * (1.0 - progress)));
    }
    let mut lifecycle = frame
        .stars
        .iter()
        .filter(|star| star.lifecycle > 0 && star.lifecycle_progress < 1.0)
        .collect::<Vec<_>>();
    lifecycle.sort_by(|left, right| left.lifecycle_progress.total_cmp(&right.lifecycle_progress));
    for star in lifecycle.into_iter().take(12) {
        let x = PLOT_LEFT + star.x;
        let y = PLOT_TOP + star.y;
        let color = match star.lifecycle {
            1 => "#75f0a9",
            2 => "#63dfff",
            _ => "#ff647c",
        };
        svg.push_str(&format!("<circle cx=\"{x:.2}\" cy=\"{y:.2}\" r=\"{:.2}\" fill=\"none\" stroke=\"{color}\" stroke-width=\"1.4\" opacity=\"{:.3}\"/>", star.diameter * 0.5 + 10.0 + 24.0 * star.lifecycle_progress, 0.86 * (1.0 - star.lifecycle_progress)));
    }
    let progress = if timeline.frames.len() <= 1 {
        1.0
    } else {
        index as f32 / (timeline.frames.len() - 1) as f32
    };
    svg.push_str(&format!("<line x1=\"32\" y1=\"791\" x2=\"1232\" y2=\"791\" stroke=\"#273343\"/><line x1=\"72\" y1=\"813\" x2=\"1122\" y2=\"813\" stroke=\"#243646\" stroke-width=\"2\"/><line x1=\"72\" y1=\"813\" x2=\"{:.2}\" y2=\"813\" stroke=\"#61d7bf\" stroke-width=\"2\"/><circle cx=\"{:.2}\" cy=\"813\" r=\"4\" fill=\"#61d7bf\"/><text x=\"32\" y=\"842\" fill=\"#8798ad\" font-family=\"ui-monospace,monospace\" font-size=\"9\">{} · frame {}/{} · {} files</text>", 72.0 + 1050.0 * progress, 72.0 + 1050.0 * progress, escape_xml(&iso_label(frame.timestamp_ms)), index + 1, timeline.frames.len(), frame.stars.len()));
    if frame.commit_flash {
        svg.push_str(&format!("<rect x=\"1.5\" y=\"1.5\" width=\"{}\" height=\"{}\" fill=\"none\" stroke=\"#efd265\" stroke-width=\"2\"/>", ARTIFACT_WIDTH - 3, ARTIFACT_HEIGHT - 3));
    }
    svg.push_str("</svg>");
    svg
}

#[derive(Clone, Copy)]
pub(crate) enum AnimationFormat {
    Gif,
    Mp4,
}

pub(crate) fn encode_animations(
    timeline: &SceneTimeline,
    outputs: &[(PathBuf, AnimationFormat)],
) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    if outputs.is_empty() {
        return Ok(());
    }
    let mut encoders = outputs
        .iter()
        .map(|(path, format)| Encoder::spawn(path, *format, timeline.fps()))
        .collect::<Result<Vec<_>, _>>()?;
    for (index, frame) in timeline.frames.iter().enumerate() {
        let pixmap = render_pixmap(timeline, frame, index);
        for encoder in &mut encoders {
            encoder.write_frame(pixmap.data())?;
        }
        let done = index + 1;
        if done % 12 == 0 || done == timeline.frames.len() {
            eprintln!(
                "[agentsight-vis] frames      {done}/{}",
                timeline.frames.len()
            );
        }
    }
    for encoder in encoders {
        encoder.finish()?;
    }
    Ok(())
}

struct Encoder {
    path: PathBuf,
    child: Child,
    stdin: Option<ChildStdin>,
}

impl Encoder {
    fn spawn(
        path: &Path,
        format: AnimationFormat,
        fps: u32,
    ) -> Result<Self, Box<dyn std::error::Error + Send + Sync>> {
        let mut command = Command::new("ffmpeg");
        command.args([
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "rawvideo",
            "-pixel_format",
            "rgba",
            "-video_size",
            &format!("{ARTIFACT_WIDTH}x{ARTIFACT_HEIGHT}"),
            "-framerate",
            &fps.to_string(),
            "-i",
            "pipe:0",
        ]);
        match format {
            AnimationFormat::Gif => {
                command.args(["-filter_complex", "[0:v]split[g0][g1];[g0]palettegen=max_colors=128[p];[g1][p]paletteuse=dither=sierra2_4a", "-loop", "0"]);
            }
            AnimationFormat::Mp4 => {
                command.args([
                    "-c:v",
                    "libx264",
                    "-vf",
                    "pad=ceil(iw/2)*2:ceil(ih/2)*2",
                    "-pix_fmt",
                    "yuv420p",
                    "-movflags",
                    "+faststart",
                ]);
            }
        }
        let mut child = command
            .arg(path)
            .stdin(Stdio::piped())
            .stdout(Stdio::null())
            .stderr(Stdio::piped())
            .spawn()?;
        let stdin = child.stdin.take().ok_or("ffmpeg did not expose stdin")?;
        Ok(Self {
            path: path.to_path_buf(),
            child,
            stdin: Some(stdin),
        })
    }

    fn write_frame(&mut self, rgba: &[u8]) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        self.stdin
            .as_mut()
            .ok_or("ffmpeg stdin already closed")?
            .write_all(rgba)?;
        Ok(())
    }

    fn finish(mut self) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
        drop(self.stdin.take());
        let status = self.child.wait()?;
        if status.success() {
            return Ok(());
        }
        let mut stderr = String::new();
        if let Some(mut pipe) = self.child.stderr.take() {
            let _ = pipe.read_to_string(&mut stderr);
        }
        Err(format!(
            "ffmpeg failed for {}: {}",
            self.path.display(),
            stderr.trim()
        )
        .into())
    }
}

fn summarize_actions(actions: &[FileAction]) -> String {
    if actions.is_empty() {
        return "no file actions".to_string();
    }
    let mut counts = [0usize; 5];
    let mut vendors = BTreeSet::new();
    for action in actions {
        counts[action_priority(action.kind)] += 1;
        vendors.insert(action.vendor.as_str());
    }
    let kinds = [
        ActionKind::Rename,
        ActionKind::Delete,
        ActionKind::Create,
        ActionKind::Write,
        ActionKind::Read,
    ];
    let detail = kinds
        .iter()
        .filter_map(|kind| {
            let count = counts[action_priority(*kind)];
            (count > 0).then(|| format!("{count} {}", kind.label()))
        })
        .collect::<Vec<_>>()
        .join(" / ");
    format!(
        "{} / {} actions / {detail}",
        vendors.into_iter().collect::<Vec<_>>().join("+"),
        actions.len()
    )
}

fn action_priority(kind: ActionKind) -> usize {
    match kind {
        ActionKind::Rename => 0,
        ActionKind::Delete => 1,
        ActionKind::Create => 2,
        ActionKind::Write => 3,
        ActionKind::Read => 4,
    }
}

fn capped_shares(rows: &[(String, Vec<u32>, f32, f32, f32)]) -> HashMap<String, f32> {
    if rows.len() == 1 {
        return HashMap::from([(rows[0].0.clone(), 1.0)]);
    }
    let cap = DIRECTORY_MAX_SHARE.max(1.0 / rows.len() as f32 + 0.08);
    let mut active = rows
        .iter()
        .map(|row| row.0.clone())
        .collect::<BTreeSet<_>>();
    let weights = rows
        .iter()
        .map(|row| (row.0.clone(), row.4))
        .collect::<HashMap<_, _>>();
    let mut shares = HashMap::new();
    let mut remaining = 1.0;
    while !active.is_empty() {
        let total = active
            .iter()
            .map(|top| weights[top])
            .sum::<f32>()
            .max(0.001);
        let oversized = active
            .iter()
            .filter(|top| remaining * weights[*top] / total > cap)
            .cloned()
            .collect::<Vec<_>>();
        if oversized.is_empty() {
            for top in active {
                shares.insert(top.clone(), remaining * weights[&top] / total);
            }
            break;
        }
        for top in oversized {
            shares.insert(top.clone(), cap);
            active.remove(&top);
            remaining -= cap;
        }
    }
    shares
}

fn current_node_color(node: &Node, frame: usize) -> [u8; 3] {
    let progress = ((frame.saturating_sub(node.color_frame) + 1) as f32 / TRANSITION_FRAMES as f32)
        .clamp(0.0, 1.0);
    [
        mix_u8(node.color_from[0], node.color_to[0], progress),
        mix_u8(node.color_from[1], node.color_to[1], progress),
        mix_u8(node.color_from[2], node.color_to[2], progress),
    ]
}

fn node_opacity(node: &Node, frame: usize) -> f32 {
    let born = ((frame.saturating_sub(node.birth_frame) + 1) as f32 / TRANSITION_FRAMES as f32)
        .clamp(0.0, 1.0);
    let deleted = node
        .delete_frame
        .map(|deleted| {
            1.0 - ((frame.saturating_sub(deleted) + 1) as f32 / TRANSITION_FRAMES as f32)
                .clamp(0.0, 1.0)
        })
        .unwrap_or(1.0);
    born * deleted
}

fn focus_strength(kind: ActionKind) -> f32 {
    match kind {
        ActionKind::Read => 0.35,
        ActionKind::Write => 0.75,
        ActionKind::Create => 1.0,
        ActionKind::Rename => 0.8,
        ActionKind::Delete => 0.9,
    }
}

fn path_parts(path: &str) -> Vec<&str> {
    path.split('/').filter(|part| !part.is_empty()).collect()
}

fn directory_parts(path: &str) -> Vec<&str> {
    let mut parts = path_parts(path);
    parts.pop();
    parts
}

fn parent_directory(path: &str) -> String {
    let parts = directory_parts(path);
    if parts.is_empty() {
        "(root)".to_string()
    } else {
        parts.join("/")
    }
}

fn top_directory(path: &str) -> String {
    let parts = path_parts(path);
    if parts.len() > 1 {
        parts[0].to_string()
    } else {
        "(root)".to_string()
    }
}

fn layout_directory(path: &str) -> String {
    let parts = directory_parts(path);
    if parts.is_empty() {
        "(root)".to_string()
    } else {
        parts[..parts.len().min(2)].join("/")
    }
}

fn common_prefix_depth(left: &[&str], right: &[&str]) -> usize {
    left.iter().zip(right).take_while(|(a, b)| a == b).count()
}

fn offset_near(x: f32, y: f32, seed: &str, distance: f32) -> (f32, f32) {
    let angle = hash_unit(&format!("{seed}:birth")) * 2.0 * PI;
    (x + distance * angle.cos(), y + distance * angle.sin())
}

fn add_centroid<K: std::hash::Hash + Eq>(
    map: &mut HashMap<K, (f32, f32, usize)>,
    key: K,
    x: f32,
    y: f32,
) {
    let row = map.entry(key).or_insert((0.0, 0.0, 0));
    row.0 += x;
    row.1 += y;
    row.2 += 1;
}

fn centroid<K: std::hash::Hash + Eq>(map: &HashMap<K, (f32, f32, usize)>, key: &K) -> (f32, f32) {
    map.get(key)
        .map(|row| (row.0 / row.2 as f32, row.1 / row.2 as f32))
        .unwrap_or_default()
}

fn add_force(forces: &mut HashMap<u32, (f32, f32)>, id: u32, x: f32, y: f32) {
    let force = forces.entry(id).or_default();
    force.0 += x;
    force.1 += y;
}

fn add_impulse(impulses: &mut HashMap<String, (f32, f32)>, key: &str, x: f32, y: f32) {
    let impulse = impulses.entry(key.to_string()).or_default();
    impulse.0 += x;
    impulse.1 += y;
}

fn hash32(value: &str) -> u32 {
    value.bytes().fold(2_166_136_261_u32, |hash, byte| {
        (hash ^ byte as u32).wrapping_mul(16_777_619)
    })
}

fn hash_unit(value: &str) -> f32 {
    hash32(value) as f32 / u32::MAX as f32
}

fn oklch_rgb(lightness: f32, chroma: f32, hue_degrees: f32) -> [u8; 3] {
    let hue = hue_degrees.to_radians();
    let a = chroma * hue.cos();
    let b = chroma * hue.sin();
    let l_root = lightness + 0.396_337_78 * a + 0.215_803_76 * b;
    let m_root = lightness - 0.105_561_346 * a - 0.063_854_17 * b;
    let s_root = lightness - 0.089_484_18 * a - 1.291_485_5 * b;
    let l = l_root.powi(3);
    let m = m_root.powi(3);
    let s = s_root.powi(3);
    [
        linear_to_srgb(4.076_741_7 * l - 3.307_711_6 * m + 0.230_969_94 * s),
        linear_to_srgb(-1.268_438 * l + 2.609_757_4 * m - 0.341_319_38 * s),
        linear_to_srgb(-0.004_196_086_3 * l - 0.703_418_6 * m + 1.707_614_7 * s),
    ]
}

fn linear_to_srgb(value: f32) -> u8 {
    let value = value.clamp(0.0, 1.0);
    let gamma = if value <= 0.003_130_8 {
        12.92 * value
    } else {
        1.055 * value.powf(1.0 / 2.4) - 0.055
    };
    (255.0 * gamma.clamp(0.0, 1.0)).round() as u8
}

fn mix_u8(left: u8, right: u8, progress: f32) -> u8 {
    (left as f32 + (right as f32 - left as f32) * progress).round() as u8
}

fn quantize_u8(value: f32) -> u8 {
    (value.clamp(0.0, 1.0) * u8::MAX as f32).round() as u8
}

fn quantize_u16(value: f32) -> u16 {
    (value.clamp(0.0, 1.0) * u16::MAX as f32).round() as u16
}

fn pack_color(color: [u8; 3]) -> u32 {
    (color[0] as u32) << 16 | (color[1] as u32) << 8 | color[2] as u32
}

fn fill_circle(pixmap: &mut Pixmap, x: f32, y: f32, radius: f32, color: [u8; 4]) {
    let Some(path) = PathBuilder::from_circle(x, y, radius.max(0.1)) else {
        return;
    };
    let mut paint = Paint::default();
    paint.set_color_rgba8(color[0], color[1], color[2], color[3]);
    paint.anti_alias = true;
    pixmap.fill_path(
        &path,
        &paint,
        FillRule::Winding,
        Transform::identity(),
        None,
    );
}

fn stroke_circle(pixmap: &mut Pixmap, x: f32, y: f32, radius: f32, color: [u8; 4], width: f32) {
    let Some(path) = PathBuilder::from_circle(x, y, radius.max(0.1)) else {
        return;
    };
    let mut paint = Paint::default();
    paint.set_color_rgba8(color[0], color[1], color[2], color[3]);
    paint.anti_alias = true;
    pixmap.stroke_path(
        &path,
        &paint,
        &Stroke {
            width,
            ..Stroke::default()
        },
        Transform::identity(),
        None,
    );
}

fn fill_rect(pixmap: &mut Pixmap, x: f32, y: f32, width: f32, height: f32, color: [u8; 4]) {
    let Some(rect) = Rect::from_xywh(x, y, width.max(0.1), height.max(0.1)) else {
        return;
    };
    let mut paint = Paint::default();
    paint.set_color_rgba8(color[0], color[1], color[2], color[3]);
    pixmap.fill_rect(rect, &paint, Transform::identity(), None);
}

fn stroke_rect(
    pixmap: &mut Pixmap,
    x: f32,
    y: f32,
    width: f32,
    height: f32,
    color: [u8; 4],
    line_width: f32,
) {
    let Some(rect) = Rect::from_xywh(x, y, width, height) else {
        return;
    };
    let path = PathBuilder::from_rect(rect);
    let mut paint = Paint::default();
    paint.set_color_rgba8(color[0], color[1], color[2], color[3]);
    pixmap.stroke_path(
        &path,
        &paint,
        &Stroke {
            width: line_width,
            ..Stroke::default()
        },
        Transform::identity(),
        None,
    );
}

fn draw_text(pixmap: &mut Pixmap, x: i32, y: i32, text: &str, scale: i32, color: [u8; 4]) {
    let mut cursor = x;
    for character in text.chars() {
        let glyph = BASIC_FONTS.get(character).or_else(|| BASIC_FONTS.get('?'));
        if let Some(glyph) = glyph {
            for (row, bits) in glyph.iter().enumerate() {
                for column in 0..8 {
                    if bits & (1 << column) != 0 {
                        fill_rect(
                            pixmap,
                            (cursor + column * scale) as f32,
                            (y + row as i32 * scale) as f32,
                            scale as f32,
                            scale as f32,
                            color,
                        );
                    }
                }
            }
        }
        cursor += 9 * scale;
        if cursor >= ARTIFACT_WIDTH as i32 - 16 {
            break;
        }
    }
}

fn iso_label(timestamp_ms: i64) -> String {
    chrono::DateTime::from_timestamp_millis(timestamp_ms)
        .map(|value| value.format("%Y-%m-%d %H:%M:%S UTC").to_string())
        .unwrap_or_else(|| timestamp_ms.to_string())
}

fn ascii_upper(value: &str) -> String {
    value
        .chars()
        .map(|character| {
            if character.is_ascii() {
                character.to_ascii_uppercase()
            } else {
                '?'
            }
        })
        .collect()
}

fn truncate_chars(value: &str, max: usize) -> String {
    if value.chars().count() <= max {
        return value.to_string();
    }
    let mut truncated = value
        .chars()
        .take(max.saturating_sub(3))
        .collect::<String>();
    truncated.push_str("...");
    truncated
}

fn escape_xml(value: &str) -> String {
    value
        .replace('&', "&amp;")
        .replace('<', "&lt;")
        .replace('>', "&gt;")
        .replace('"', "&quot;")
}

#[cfg(test)]
mod tests {
    use super::*;

    fn sample_input() -> SceneInput {
        SceneInput {
            repository: "demo".to_string(),
            revision: "0123456789abcdef".to_string(),
            window_start_ms: 1_000,
            window_end_ms: 4_000,
            session_scope: "repository_identity".to_string(),
            session_count: 2,
            actions: vec![
                FileAction {
                    event_id: "one".into(),
                    session_id: "s1".into(),
                    vendor: "codex".into(),
                    timestamp_ms: 2_000,
                    kind: ActionKind::Create,
                    path: "src/main.rs".into(),
                    old_path: None,
                },
                FileAction {
                    event_id: "two".into(),
                    session_id: "s2".into(),
                    vendor: "claude".into(),
                    timestamp_ms: 3_000,
                    kind: ActionKind::Read,
                    path: "src/main.rs".into(),
                    old_path: None,
                },
            ],
            commit_times: vec![2_500],
        }
    }

    #[test]
    fn timeline_starts_empty_and_preserves_event_steps() {
        let timeline = build_timeline(sample_input());
        assert_eq!(timeline.frames.len(), 3);
        assert!(timeline.frames[0].stars.is_empty());
        assert_eq!(timeline.frames[1].stars.len(), 1);
        assert!(timeline.frames[2].commit_flash);
    }

    #[test]
    fn raster_and_svg_share_artifact_dimensions() {
        let timeline = build_timeline(sample_input());
        let pixmap = render_pixmap(&timeline, timeline.final_frame(), timeline.frames.len() - 1);
        assert_eq!(pixmap.width(), ARTIFACT_WIDTH);
        assert_eq!(pixmap.height(), ARTIFACT_HEIGHT);
        let svg = svg_document(&timeline);
        assert!(svg.contains("width=\"1264\""));
        assert!(svg.contains("Repository Nebula"));
    }

    #[test]
    fn html_is_self_contained_canvas_without_browser_chart_runtime() {
        let timeline = build_timeline(sample_input());
        let html = html_document(&timeline).unwrap();
        assert!(html.contains("<canvas id=\"chart\""));
        assert!(html.contains("window.__AGENTSIGHT_READY__"));
        assert!(!html.contains("AgentSightSingle"));
        assert!(!html.contains("echarts"));
    }
}

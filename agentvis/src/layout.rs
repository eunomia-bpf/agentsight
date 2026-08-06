// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

//! Server-side Agent Nebula layout.
//!
//! Builds a compact, bounded frame document from repository file actions so
//! browsers only render. Positions, colors, and per-moment deltas are computed
//! once here; the client keeps interaction state only.

use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, HashMap, HashSet};

/// Default caps for the web payload. Long sessions must not produce unbounded JSON.
pub const DEFAULT_MAX_STARS: usize = 1_500;
pub const DEFAULT_MAX_FRAMES: usize = 400;

const GOLDEN_ANGLE: f64 = 137.508_f64.to_radians();
const RESTING_MIN: f64 = 0.85;
const RESTING_MAX: f64 = 6.0;
const FOCUSED_MAX: f64 = 10.5;
const RESTING_REFERENCE: f64 = 480.0;

#[derive(Debug, Clone)]
pub struct NebulaLayoutOptions {
    pub max_stars: usize,
    pub max_frames: usize,
    pub repository: String,
}

impl Default for NebulaLayoutOptions {
    fn default() -> Self {
        Self {
            max_stars: DEFAULT_MAX_STARS,
            max_frames: DEFAULT_MAX_FRAMES,
            repository: "session".into(),
        }
    }
}

/// One file action observed in session time order.
#[derive(Debug, Clone)]
pub struct NebulaFileAction {
    pub ts_ms: u64,
    pub path: String,
    /// Collector/action label: write, read, create, rename, delete, observed, …
    pub access: String,
    pub previous_path: Option<String>,
    pub event_id: String,
    pub pid: Option<u32>,
    pub comm: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NebulaDocument {
    pub meta: NebulaMeta,
    pub areas: Vec<NebulaArea>,
    pub stars: Vec<NebulaStar>,
    pub frames: Vec<NebulaFrame>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NebulaMeta {
    pub repository: String,
    pub source: String,
    pub window_start_ms: Option<u64>,
    pub window_end_ms: Option<u64>,
    pub total_file_events: usize,
    pub total_unique_files: usize,
    pub shown_stars: usize,
    pub shown_frames: usize,
    pub max_stars: usize,
    pub max_frames: usize,
    /// Human-readable bound policy so the UI can say "showing N of M".
    pub bounding_policy: String,
    pub empty: bool,
    pub empty_reason: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NebulaArea {
    pub name: String,
    pub color: String,
    pub count: usize,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NebulaStar {
    pub id: u16,
    pub path: String,
    pub area: String,
    /// Normalized canvas coordinates in \[0, 1\].
    pub x: f64,
    pub y: f64,
    pub color: String,
    pub first_ms: u64,
    pub last_ms: u64,
    pub visits: u32,
    /// Frame index when this star first appears (inclusive).
    pub birth_frame: u16,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NebulaFrame {
    pub index: u16,
    pub t_ms: u64,
    pub summary: String,
    /// Stars touched in this moment (subset of shown stars).
    pub active: Vec<NebulaActive>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NebulaActive {
    pub id: u16,
    pub access: String,
    pub strength: f32,
}

/// Project ordered file actions into a bounded nebula document.
pub fn build_nebula_document(
    actions: &[NebulaFileAction],
    options: &NebulaLayoutOptions,
) -> NebulaDocument {
    let max_stars = options.max_stars.max(1);
    let max_frames = options.max_frames.max(1);
    let policy = format!(
        "stars: keep top {max_stars} by visit count then recency; \
         frames: uniform sample of at most {max_frames} action moments across session time"
    );

    if actions.is_empty() {
        return empty_document(options, policy, "No file events in this session");
    }

    // Aggregate per-path stats. Each audit row is its own visual moment so a
    // burst of same-millisecond writes still plays back as repository evolution
    // rather than collapsing into a handful of frames.
    let mut path_stats: BTreeMap<String, PathStats> = BTreeMap::new();
    let mut moments: Vec<Moment> = Vec::new();

    for action in actions {
        let path = normalize_path(&action.path);
        if path.is_empty() {
            continue;
        }
        let access = normalize_access(&action.access);
        let stats = path_stats.entry(path.clone()).or_insert_with(|| PathStats {
            first_ms: action.ts_ms,
            last_ms: action.ts_ms,
            visits: 0,
            last_access: access.clone(),
        });
        stats.visits = stats.visits.saturating_add(1);
        stats.last_ms = action.ts_ms;
        stats.last_access = access.clone();

        moments.push(Moment {
            t_ms: action.ts_ms,
            hits: vec![Hit {
                path: path.clone(),
                access: access.clone(),
            }],
            summary_parts: vec![format!("{access} · {path}")],
        });
    }

    if path_stats.is_empty() || moments.is_empty() {
        return empty_document(options, policy, "No file paths found in file events");
    }

    let total_file_events = actions.len();
    let total_unique_files = path_stats.len();

    // Cap stars: rank by visits desc, then last_ms desc, then path.
    let mut ranked: Vec<(String, PathStats)> = path_stats.into_iter().collect();
    ranked.sort_by(|a, b| {
        b.1.visits
            .cmp(&a.1.visits)
            .then_with(|| b.1.last_ms.cmp(&a.1.last_ms))
            .then_with(|| a.0.cmp(&b.0))
    });
    if ranked.len() > max_stars {
        ranked.truncate(max_stars);
    }
    let kept: HashSet<String> = ranked.iter().map(|(p, _)| p.clone()).collect();

    // Area palette + stable positions.
    let mut area_names: Vec<String> = ranked
        .iter()
        .map(|(path, _)| root_area(path))
        .collect::<HashSet<_>>()
        .into_iter()
        .collect();
    area_names.sort();
    let seed_hue = hash_unit(&options.repository) * 360.0;
    let area_hue: HashMap<String, f64> = area_names
        .iter()
        .enumerate()
        .map(|(rank, name)| {
            (
                name.clone(),
                (seed_hue + GOLDEN_ANGLE.to_degrees() * rank as f64) % 360.0,
            )
        })
        .collect();

    // Place area centers on a ring, then spiral files within each area.
    let area_centers: HashMap<String, (f64, f64)> = {
        let n = area_names.len().max(1) as f64;
        area_names
            .iter()
            .enumerate()
            .map(|(i, name)| {
                let angle = GOLDEN_ANGLE * i as f64 + hash_unit(name) * 0.35;
                let radius = 0.18 + 0.22 * (1.0 - 1.0 / n.sqrt());
                let cx = 0.5 + radius * angle.cos();
                let cy = 0.5 + radius * angle.sin();
                (name.clone(), (cx.clamp(0.08, 0.92), cy.clamp(0.08, 0.92)))
            })
            .collect()
    };

    let mut by_area: HashMap<String, Vec<usize>> = HashMap::new();
    for (idx, (path, _)) in ranked.iter().enumerate() {
        by_area.entry(root_area(path)).or_default().push(idx);
    }
    for members in by_area.values_mut() {
        members.sort_by(|&a, &b| ranked[a].0.cmp(&ranked[b].0));
    }

    let mut positions: Vec<(f64, f64)> = vec![(0.5, 0.5); ranked.len()];
    for (area, members) in &by_area {
        let (cx, cy) = area_centers.get(area).copied().unwrap_or((0.5, 0.5));
        let count = members.len().max(1) as f64;
        let spread = (0.04 + 0.12 * (count.sqrt() / 12.0)).min(0.22);
        for (rank, &idx) in members.iter().enumerate() {
            let path = &ranked[idx].0;
            let angle = GOLDEN_ANGLE * rank as f64 + hash_unit(path) * std::f64::consts::TAU;
            let ring = ((rank as f64 + 1.0) / count).sqrt() * spread;
            let jitter = 0.008 * (hash_unit(&format!("{path}:j")) * 2.0 - 1.0);
            let x = (cx + (ring + jitter) * angle.cos()).clamp(0.03, 0.97);
            let y = (cy + (ring + jitter) * angle.sin()).clamp(0.03, 0.97);
            positions[idx] = (x, y);
        }
    }

    // Downsample moments to max_frames (uniform over indices).
    let frame_indices = sample_indices(moments.len(), max_frames);
    let mut birth_frame: HashMap<String, u16> = HashMap::new();
    let mut stars_out: Vec<NebulaStar> = Vec::with_capacity(ranked.len());
    let mut path_to_id: HashMap<String, u16> = HashMap::new();

    // First pass: discover birth frame for each kept path.
    for (frame_i, &moment_i) in frame_indices.iter().enumerate() {
        let moment = &moments[moment_i];
        for hit in &moment.hits {
            if !kept.contains(&hit.path) {
                continue;
            }
            birth_frame
                .entry(hit.path.clone())
                .or_insert(frame_i as u16);
        }
    }
    // Paths never hit after downsampling still get a birth at last frame if they had visits.
    for (path, _) in &ranked {
        birth_frame.entry(path.clone()).or_insert(0);
    }

    for (idx, (path, stats)) in ranked.iter().enumerate() {
        let area = root_area(path);
        let hue = area_hue.get(&area).copied().unwrap_or(seed_hue);
        let depth = path_parts(path).len().saturating_sub(1) as f64;
        let lightness = (0.58 + 0.055 * depth).min(0.84);
        let chroma = (0.17 - 0.015 * depth).max(0.08);
        let color = oklch_rgb_string(lightness, chroma, hue);
        let id = idx as u16;
        path_to_id.insert(path.clone(), id);
        let (x, y) = positions[idx];
        stars_out.push(NebulaStar {
            id,
            path: path.clone(),
            area: area.clone(),
            x,
            y,
            color,
            first_ms: stats.first_ms,
            last_ms: stats.last_ms,
            visits: stats.visits,
            birth_frame: *birth_frame.get(path).unwrap_or(&0),
        });
    }

    let mut area_counts: BTreeMap<String, usize> = BTreeMap::new();
    for star in &stars_out {
        *area_counts.entry(star.area.clone()).or_default() += 1;
    }
    let areas: Vec<NebulaArea> = area_names
        .iter()
        .filter_map(|name| {
            let count = *area_counts.get(name)?;
            let hue = area_hue.get(name).copied().unwrap_or(seed_hue);
            Some(NebulaArea {
                name: name.clone(),
                color: oklch_rgb_string(0.62, 0.14, hue),
                count,
            })
        })
        .collect();

    let mut frames: Vec<NebulaFrame> = Vec::with_capacity(frame_indices.len());
    for (frame_i, &moment_i) in frame_indices.iter().enumerate() {
        let moment = &moments[moment_i];
        let mut active: Vec<NebulaActive> = Vec::new();
        let mut seen = HashSet::new();
        for hit in &moment.hits {
            let Some(&id) = path_to_id.get(&hit.path) else {
                continue;
            };
            if !seen.insert(id) {
                continue;
            }
            let strength = match hit.access.as_str() {
                "create" | "rename" | "delete" => 1.0,
                "write" => 0.85,
                "read" => 0.55,
                _ => 0.7,
            };
            active.push(NebulaActive {
                id,
                access: hit.access.clone(),
                strength,
            });
        }
        let summary = if moment.summary_parts.is_empty() {
            format!("{} file actions", moment.hits.len())
        } else {
            let extra = moment.hits.len().saturating_sub(moment.summary_parts.len());
            let mut text = moment.summary_parts.join(" · ");
            if extra > 0 {
                text.push_str(&format!(" · +{extra} more"));
            }
            text
        };
        frames.push(NebulaFrame {
            index: frame_i as u16,
            t_ms: moment.t_ms,
            summary,
            active,
        });
    }

    let window_start_ms = frames
        .first()
        .map(|f| f.t_ms)
        .or_else(|| actions.first().map(|a| a.ts_ms));
    let window_end_ms = frames
        .last()
        .map(|f| f.t_ms)
        .or_else(|| actions.last().map(|a| a.ts_ms));

    NebulaDocument {
        meta: NebulaMeta {
            repository: options.repository.clone(),
            source: "audit_events.file".into(),
            window_start_ms,
            window_end_ms,
            total_file_events,
            total_unique_files,
            shown_stars: stars_out.len(),
            shown_frames: frames.len(),
            max_stars,
            max_frames,
            bounding_policy: policy,
            empty: false,
            empty_reason: None,
        },
        areas,
        stars: stars_out,
        frames,
    }
}

/// Resting symbol size for a star given total visible count and visit weight.
pub fn resting_symbol_size(visits: u32, visible_count: usize) -> f64 {
    let density = (RESTING_REFERENCE / RESTING_REFERENCE.max(visible_count as f64)).sqrt();
    let base = (RESTING_MAX * density).clamp(RESTING_MIN, RESTING_MAX);
    let weight = (0.62 + 0.38 * (visits as f64).sqrt().min(4.0) / 2.0).clamp(0.62, 1.4);
    (base * weight).clamp(RESTING_MIN, FOCUSED_MAX)
}

fn empty_document(options: &NebulaLayoutOptions, policy: String, reason: &str) -> NebulaDocument {
    NebulaDocument {
        meta: NebulaMeta {
            repository: options.repository.clone(),
            source: "audit_events.file".into(),
            window_start_ms: None,
            window_end_ms: None,
            total_file_events: 0,
            total_unique_files: 0,
            shown_stars: 0,
            shown_frames: 0,
            max_stars: options.max_stars,
            max_frames: options.max_frames,
            bounding_policy: policy,
            empty: true,
            empty_reason: Some(reason.into()),
        },
        areas: Vec::new(),
        stars: Vec::new(),
        frames: Vec::new(),
    }
}

#[derive(Clone)]
struct PathStats {
    first_ms: u64,
    last_ms: u64,
    visits: u32,
    last_access: String,
}

struct Moment {
    t_ms: u64,
    hits: Vec<Hit>,
    summary_parts: Vec<String>,
}

struct Hit {
    path: String,
    access: String,
}

fn sample_indices(total: usize, max: usize) -> Vec<usize> {
    if total == 0 {
        return Vec::new();
    }
    if total <= max {
        return (0..total).collect();
    }
    if max == 1 {
        return vec![total - 1];
    }
    (0..max)
        .map(|frame| frame * (total - 1) / (max - 1))
        .collect()
}

fn normalize_path(path: &str) -> String {
    let trimmed = path.trim().trim_start_matches("./");
    if trimmed.is_empty() || trimmed == "." {
        return String::new();
    }
    // Prefer a short display path: drop leading absolute noise when deep.
    let parts: Vec<&str> = trimmed.split('/').filter(|p| !p.is_empty()).collect();
    if parts.len() > 6 && trimmed.starts_with('/') {
        // keep last 5 components for area clustering of absolute paths
        return parts[parts.len().saturating_sub(5)..].join("/");
    }
    parts.join("/")
}

fn normalize_access(access: &str) -> String {
    let lower = access.trim().to_ascii_lowercase();
    match lower.as_str() {
        "read" | "write" | "create" | "rename" | "delete" | "observed" => lower,
        "open" | "fs_open" | "file_open" => "write".into(),
        "unlink" | "rm" => "delete".into(),
        "mkdir" | "touch" => "create".into(),
        "" => "write".into(),
        other => other.into(),
    }
}

fn path_parts(path: &str) -> Vec<&str> {
    path.split('/').filter(|p| !p.is_empty()).collect()
}

fn root_area(path: &str) -> String {
    path_parts(path)
        .first()
        .map(|s| (*s).to_string())
        .unwrap_or_else(|| "(root)".into())
}

fn hash32(value: &str) -> u32 {
    let mut hash: u32 = 2_166_136_261;
    for byte in value.bytes() {
        hash ^= u32::from(byte);
        hash = hash.wrapping_mul(16_777_619);
    }
    hash
}

fn hash_unit(value: &str) -> f64 {
    f64::from(hash32(value)) / f64::from(u32::MAX)
}

fn clamp01(value: f64) -> f64 {
    value.clamp(0.0, 1.0)
}

fn srgb_channel(value: f64) -> u8 {
    let linear = clamp01(value);
    let gamma = if linear <= 0.003_130_8 {
        12.92 * linear
    } else {
        1.055 * linear.powf(1.0 / 2.4) - 0.055
    };
    (255.0 * clamp01(gamma)).round() as u8
}

fn oklch_rgb_string(lightness: f64, chroma: f64, hue_degrees: f64) -> String {
    let hue = hue_degrees.to_radians();
    let a = chroma * hue.cos();
    let b = chroma * hue.sin();
    let l_root = lightness + 0.396_337_777_4 * a + 0.215_803_757_3 * b;
    let m_root = lightness - 0.105_561_345_8 * a - 0.063_854_172_8 * b;
    let s_root = lightness - 0.089_484_177_5 * a - 1.291_485_548 * b;
    let l = l_root.powi(3);
    let m = m_root.powi(3);
    let s = s_root.powi(3);
    let r = srgb_channel(4.076_741_662_1 * l - 3.307_711_591_3 * m + 0.230_969_929_2 * s);
    let g = srgb_channel(-1.268_438_004_6 * l + 2.609_757_401_1 * m - 0.341_319_396_5 * s);
    let bl = srgb_channel(-0.004_196_086_3 * l - 0.703_418_614_7 * m + 1.707_614_701 * s);
    format!("rgb({r} {g} {bl})")
}

#[cfg(test)]
mod tests {
    use super::*;

    fn action(ts: u64, path: &str, access: &str) -> NebulaFileAction {
        NebulaFileAction {
            ts_ms: ts,
            path: path.into(),
            access: access.into(),
            previous_path: None,
            event_id: format!("e-{ts}-{path}"),
            pid: Some(1),
            comm: Some("agent".into()),
        }
    }

    #[test]
    fn empty_session_is_honest() {
        let doc = build_nebula_document(&[], &NebulaLayoutOptions::default());
        assert!(doc.meta.empty);
        assert!(doc.stars.is_empty());
        assert!(doc.frames.is_empty());
        assert!(doc.meta.empty_reason.is_some());
    }

    #[test]
    fn builds_stars_and_frames_from_writes() {
        let actions = vec![
            action(1000, "src/main.rs", "write"),
            action(1100, "src/lib.rs", "write"),
            action(1200, "src/main.rs", "write"),
            action(1300, "docs/readme.md", "write"),
            action(1400, "src/main.rs", "write"),
        ];
        let doc = build_nebula_document(
            &actions,
            &NebulaLayoutOptions {
                max_stars: 100,
                max_frames: 100,
                repository: "demo".into(),
            },
        );
        assert!(!doc.meta.empty);
        assert_eq!(doc.meta.total_file_events, 5);
        assert_eq!(doc.meta.total_unique_files, 3);
        assert_eq!(doc.stars.len(), 3);
        assert!(!doc.frames.is_empty());
        assert!(doc.areas.iter().any(|a| a.name == "src"));
        let main = doc.stars.iter().find(|s| s.path == "src/main.rs").unwrap();
        assert_eq!(main.visits, 3);
        assert!((0.0..=1.0).contains(&main.x));
        assert!((0.0..=1.0).contains(&main.y));
    }

    #[test]
    fn bounds_stars_and_frames() {
        let mut actions = Vec::new();
        for i in 0..200 {
            actions.push(action(
                1000 + i * 10,
                &format!("area{}/file{i}.rs", i % 5),
                "write",
            ));
        }
        let doc = build_nebula_document(
            &actions,
            &NebulaLayoutOptions {
                max_stars: 20,
                max_frames: 10,
                repository: "bound".into(),
            },
        );
        assert_eq!(doc.meta.total_unique_files, 200);
        assert_eq!(doc.stars.len(), 20);
        assert_eq!(doc.frames.len(), 10);
        assert_eq!(doc.meta.shown_stars, 20);
        assert_eq!(doc.meta.shown_frames, 10);
    }

    #[test]
    fn positions_are_deterministic() {
        let actions = vec![action(1, "a/x.rs", "write"), action(2, "b/y.rs", "write")];
        let opts = NebulaLayoutOptions {
            max_stars: 10,
            max_frames: 10,
            repository: "same".into(),
        };
        let left = build_nebula_document(&actions, &opts);
        let right = build_nebula_document(&actions, &opts);
        assert_eq!(left.stars[0].x, right.stars[0].x);
        assert_eq!(left.stars[0].y, right.stars[0].y);
        assert_eq!(left.stars[0].color, right.stars[0].color);
    }
}

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use super::payload::{EtwProcessPhase, ProcessEtwRecord};
use std::collections::{BTreeSet, HashMap, HashSet, VecDeque};

const TRACKER_COMPACTION_INTERVAL: u64 = 1_024;
const RECENT_EXITED_MEMBER_LIMIT: usize = 1_024;
const RETAINED_NONMEMBER_INSTANCE_LIMIT: usize = 4_096;
const AMBIGUOUS_PARENT_PID_LIMIT: usize = 1_024;
const MAX_TRACKED_INSTANCES: usize = 65_536;

#[derive(Debug, Clone, PartialEq, Eq)]
pub(super) enum PidAttribution {
    Member {
        instance_id: u64,
        comm: Option<String>,
    },
    Filtered,
    Unresolved,
    Ambiguous,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(super) enum IngestOutcome {
    Accepted {
        instance_id: u64,
        is_start: bool,
        topology_changed: bool,
    },
    Filtered,
    Duplicate,
}

#[derive(Debug, Clone)]
struct TrackedProcess {
    id: u64,
    #[allow(dead_code)]
    pid: u32,
    ppid: Option<u32>,
    session_id: Option<u32>,
    unique_process_key: Option<u64>,
    image_file_name: Option<String>,
    parent_instance: Option<u64>,
    member: bool,
    // A child Start older than this boundary cannot belong to this PID generation.
    generation_started_at: Option<i64>,
    first_start_observed_at: Option<i64>,
    first_rundown_observed_at: Option<i64>,
    seen_start: bool,
    start_announced: bool,
    seen_exit: bool,
    terminate_announced: bool,
    end_announced: bool,
    present_at_stop_announced: bool,
}

#[derive(Debug)]
struct AmbiguousExitWitnesses {
    instance_ids: HashSet<u64>,
    complete: bool,
}

#[derive(Debug)]
pub(super) struct ProcessTracker {
    root_instance: u64,
    next_instance: u64,
    instances: HashMap<u64, TrackedProcess>,
    instances_by_key: HashMap<u64, u64>,
    children_by_parent: HashMap<u64, HashSet<u64>>,
    unresolved_by_ppid: HashMap<u32, HashSet<u64>>,
    live_pid_instance: HashMap<u32, u64>,
    // Constant-time ambiguity reconciliation; the instance map remains the source of truth.
    live_pid_counts: HashMap<u32, usize>,
    ambiguous_parent_pids: HashMap<u32, u64>,
    ambiguous_parent_order: VecDeque<(u32, u64)>,
    sticky_ambiguous_parent_pids: HashSet<u32>,
    ambiguous_exit_witnesses: HashMap<u32, AmbiguousExitWitnesses>,
    recent_exited_members: HashMap<u32, u64>,
    recent_exited_member_order: VecDeque<(u32, u64)>,
    retained_nonmember_ids: HashSet<u64>,
    retained_nonmember_order: VecDeque<u64>,
    recent_exited_member_limit: usize,
    retained_nonmember_instance_limit: usize,
    ambiguous_parent_pid_limit: usize,
    max_tracked_instances: usize,
    instance_order: BTreeSet<u64>,
    next_ambiguity_token: u64,
    pid_reuse_count: u64,
    unknown_parent_count: u64,
    exited_since_compaction: u64,
    evicted_instance_count: u64,
    evicted_instance_ids: VecDeque<u64>,
    evicted_ambiguous_parent_count: u64,
    evicted_member_instance_count: u64,
}

#[derive(Debug, Clone, Copy, Default)]
pub(super) struct TrackerStats {
    pub(super) pid_reuse_count: u64,
    pub(super) unknown_parent_count: u64,
    pub(super) evicted_instance_count: u64,
    pub(super) evicted_ambiguous_parent_count: u64,
    pub(super) evicted_member_instance_count: u64,
}

impl ProcessTracker {
    pub(super) fn new(root_pid: u32) -> Self {
        Self::new_with_limits(
            root_pid,
            RECENT_EXITED_MEMBER_LIMIT,
            RETAINED_NONMEMBER_INSTANCE_LIMIT,
            AMBIGUOUS_PARENT_PID_LIMIT,
            MAX_TRACKED_INSTANCES,
        )
    }

    fn new_with_limits(
        root_pid: u32,
        recent_exited_member_limit: usize,
        retained_nonmember_instance_limit: usize,
        ambiguous_parent_pid_limit: usize,
        max_tracked_instances: usize,
    ) -> Self {
        let root_instance = 0;
        let mut instances = HashMap::new();
        instances.insert(
            root_instance,
            TrackedProcess {
                id: root_instance,
                pid: root_pid,
                ppid: None,
                session_id: None,
                unique_process_key: None,
                image_file_name: None,
                parent_instance: None,
                member: true,
                generation_started_at: None,
                first_start_observed_at: None,
                first_rundown_observed_at: None,
                seen_start: false,
                start_announced: false,
                seen_exit: false,
                terminate_announced: false,
                end_announced: false,
                present_at_stop_announced: false,
            },
        );
        let mut live_pid_instance = HashMap::new();
        live_pid_instance.insert(root_pid, root_instance);
        let live_pid_counts = HashMap::from([(root_pid, 1)]);

        Self {
            root_instance,
            next_instance: 1,
            instances,
            instances_by_key: HashMap::new(),
            children_by_parent: HashMap::new(),
            unresolved_by_ppid: HashMap::new(),
            live_pid_instance,
            live_pid_counts,
            ambiguous_parent_pids: HashMap::new(),
            ambiguous_parent_order: VecDeque::new(),
            sticky_ambiguous_parent_pids: HashSet::new(),
            ambiguous_exit_witnesses: HashMap::new(),
            recent_exited_members: HashMap::new(),
            recent_exited_member_order: VecDeque::new(),
            retained_nonmember_ids: HashSet::new(),
            retained_nonmember_order: VecDeque::new(),
            recent_exited_member_limit,
            retained_nonmember_instance_limit,
            ambiguous_parent_pid_limit,
            max_tracked_instances,
            instance_order: BTreeSet::from([root_instance]),
            next_ambiguity_token: 1,
            pid_reuse_count: 0,
            unknown_parent_count: 0,
            exited_since_compaction: 0,
            evicted_instance_count: 0,
            evicted_instance_ids: VecDeque::new(),
            evicted_ambiguous_parent_count: 0,
            evicted_member_instance_count: 0,
        }
    }

    pub(super) fn root_pid(&self) -> u32 {
        self.instances
            .get(&self.root_instance)
            .map(|process| process.pid)
            .expect("root instance exists")
    }

    fn resolve_instance_for_start(
        &mut self,
        record: &ProcessEtwRecord,
        phase: EtwProcessPhase,
        event_timestamp: Option<i64>,
    ) -> u64 {
        if let Some(key) = record.unique_process_key
            && let Some(id) = self.instances_by_key.get(&key).copied()
        {
            if !self
                .instances
                .get(&id)
                .is_some_and(|process| process.seen_exit)
            {
                return id;
            }
            // UniqueProcessKey identifies the current process object by kernel
            // address. Retained exited instances can outlive that address, so
            // a later Start with the same key is a new instance.
            self.instances_by_key.remove(&key);
        }

        if let Some(existing) = self.live_pid_instance.get(&record.pid).copied() {
            if existing == self.root_instance {
                let process = self
                    .instances
                    .get_mut(&existing)
                    .expect("root instance exists");
                if phase == EtwProcessPhase::DCStart && !process.seen_start {
                    if let Some(key) = record.unique_process_key {
                        process.unique_process_key = Some(key);
                        self.instances_by_key.insert(key, existing);
                    }
                    return existing;
                }
            }
            let existing_key = self
                .instances
                .get(&existing)
                .and_then(|p| p.unique_process_key);
            if record.unique_process_key.is_none()
                && existing_key.is_none()
                && self.instances.get(&existing).is_some_and(|process| {
                    phase == EtwProcessPhase::DCStart
                        || (phase == EtwProcessPhase::Start
                            && event_timestamp.is_some()
                            && (process.first_start_observed_at == event_timestamp
                                || (process.first_start_observed_at.is_none()
                                    && process.first_rundown_observed_at.is_some())))
                })
            {
                return existing;
            }
            if existing_key.is_none() {
                self.pid_reuse_count += 1;
            }
            if existing_key.is_some() && existing_key == record.unique_process_key {
                return existing;
            }
            if existing_key.is_some() {
                self.pid_reuse_count += 1;
            }
            self.insert_ambiguous_parent_pid(record.pid);
        }

        let id = self.next_instance;
        self.next_instance += 1;
        self.clear_recent_exited_member(record.pid);
        self.instances.insert(
            id,
            TrackedProcess {
                id,
                pid: record.pid,
                ppid: record.ppid,
                session_id: record.session_id,
                unique_process_key: record.unique_process_key,
                image_file_name: record.image_file_name.clone(),
                parent_instance: None,
                member: false,
                generation_started_at: None,
                first_start_observed_at: None,
                first_rundown_observed_at: None,
                seen_start: false,
                start_announced: false,
                seen_exit: false,
                terminate_announced: false,
                end_announced: false,
                present_at_stop_announced: false,
            },
        );
        self.instance_order.insert(id);
        if let Some(key) = record.unique_process_key {
            self.instances_by_key.insert(key, id);
        }
        self.live_pid_instance.insert(record.pid, id);
        *self.live_pid_counts.entry(record.pid).or_default() += 1;
        self.retain_nonmember_instance(id);
        self.enforce_retained_nonmember_instance_limit();
        id
    }

    #[cfg(test)]
    pub(super) fn ingest(
        &mut self,
        record: ProcessEtwRecord,
        phase: EtwProcessPhase,
    ) -> IngestOutcome {
        self.ingest_at(record, phase, None)
    }

    pub(super) fn ingest_at(
        &mut self,
        record: ProcessEtwRecord,
        phase: EtwProcessPhase,
        event_timestamp: Option<i64>,
    ) -> IngestOutcome {
        if phase == EtwProcessPhase::Unknown {
            return IngestOutcome::Filtered;
        }

        if phase.is_start() {
            let id = self.resolve_instance_for_start(&record, phase, event_timestamp);
            let Some(process) = self.instances.get_mut(&id) else {
                return IngestOutcome::Filtered;
            };
            process.ppid = record.ppid.or(process.ppid);
            process.session_id = record.session_id.or(process.session_id);
            if record.image_file_name.is_some() {
                process.image_file_name = record.image_file_name.clone();
            }
            if phase == EtwProcessPhase::Start {
                if process.first_start_observed_at.is_none() {
                    process.first_start_observed_at = event_timestamp;
                }
                if process.generation_started_at.is_none() {
                    process.generation_started_at = event_timestamp;
                }
            } else if process.first_rundown_observed_at.is_none() {
                process.first_rundown_observed_at = event_timestamp;
            }
            if process.seen_start && process.start_announced {
                return IngestOutcome::Duplicate;
            }
            process.seen_start = true;
            self.link_parent(id);
            if self
                .instances
                .get(&id)
                .is_some_and(|process| process.member)
            {
                self.promote_member_subtree(id);
            }
            let Some(process) = self.instances.get_mut(&id) else {
                return IngestOutcome::Filtered;
            };
            if !process.member {
                self.enforce_tracked_instance_limit();
                return IngestOutcome::Filtered;
            }
            if process.start_announced {
                return IngestOutcome::Duplicate;
            }
            process.start_announced = true;
            self.enforce_tracked_instance_limit();
            return IngestOutcome::Accepted {
                instance_id: id,
                is_start: true,
                topology_changed: true,
            };
        }

        let keyless_ambiguous = record.unique_process_key.is_none()
            && self.ambiguous_parent_pids.contains_key(&record.pid);
        let id = match record.unique_process_key {
            Some(key) => self.instances_by_key.get(&key).copied(),
            None if keyless_ambiguous => {
                self.unique_ambiguous_exit_candidate(&record, event_timestamp)
            }
            None => self
                .live_pid_instance
                .get(&record.pid)
                .copied()
                .or_else(|| self.recent_exited_members.get(&record.pid).copied()),
        };
        let Some(id) = id else {
            if keyless_ambiguous
                && matches!(phase, EtwProcessPhase::End | EtwProcessPhase::Terminate)
            {
                // A later keyed exit cannot prove which generation owned this
                // keyless event. Keep the PID ambiguous until a uniquely
                // attributable replay arrives or the capture ends.
                self.mark_sticky_ambiguous_parent_pid(record.pid);
            }
            if phase == EtwProcessPhase::Terminate && !keyless_ambiguous {
                return IngestOutcome::Duplicate;
            }
            return IngestOutcome::Filtered;
        };
        let Some(process) = self.instances.get_mut(&id) else {
            return IngestOutcome::Filtered;
        };
        let stale_exit = matches!(phase, EtwProcessPhase::End | EtwProcessPhase::Terminate)
            && event_timestamp
                .zip(process.generation_started_at)
                .is_some_and(|(exit_at, started_at)| exit_at <= started_at);
        if stale_exit {
            // An exit older than the current generation belongs to a prior
            // process that reused either the PID or the provider's process key
            // and must not close this instance.
            return IngestOutcome::Duplicate;
        }
        let is_member = process.member;
        if phase == EtwProcessPhase::DCEnd {
            if !is_member {
                return IngestOutcome::Filtered;
            }
            if process.present_at_stop_announced {
                return IngestOutcome::Duplicate;
            }
            process.present_at_stop_announced = true;
            return IngestOutcome::Accepted {
                instance_id: id,
                is_start: false,
                topology_changed: false,
            };
        }
        if !is_member && record.unique_process_key.is_none() {
            if keyless_ambiguous
                && matches!(phase, EtwProcessPhase::End | EtwProcessPhase::Terminate)
            {
                self.mark_sticky_ambiguous_parent_pid(record.pid);
            }
            // The parent may still arrive later and make this a member. Do not
            // consume its live mapping or mark it exited before that promotion.
            return IngestOutcome::Filtered;
        }
        let already_announced = match phase {
            EtwProcessPhase::Terminate => process.end_announced || process.terminate_announced,
            EtwProcessPhase::End => process.end_announced,
            _ => false,
        };
        if already_announced {
            return IngestOutcome::Duplicate;
        }
        let newly_exited = !process.seen_exit;
        process.seen_exit = true;
        let tracked_pid = process.pid;
        if newly_exited {
            self.decrement_live_pid_count(tracked_pid);
        }
        if self.live_pid_instance.get(&record.pid) == Some(&id) {
            self.live_pid_instance.remove(&record.pid);
        }
        if tracked_pid != record.pid && self.live_pid_instance.get(&tracked_pid) == Some(&id) {
            self.live_pid_instance.remove(&tracked_pid);
        }
        if is_member {
            self.retain_recent_exited_member(tracked_pid, id);
            let Some(process) = self.instances.get_mut(&id) else {
                return IngestOutcome::Filtered;
            };
            if phase == EtwProcessPhase::Terminate {
                process.terminate_announced = true;
            } else {
                process.end_announced = true;
            }
        } else {
            self.retain_nonmember_instance(id);
            self.enforce_retained_nonmember_instance_limit();
        }
        if newly_exited {
            self.exited_since_compaction += 1;
        }
        if self.exited_since_compaction >= TRACKER_COMPACTION_INTERVAL {
            self.compact_exited_instances();
        }
        let mut topology_changed = self.reconcile_pid_ambiguity(tracked_pid);
        if record.pid != tracked_pid {
            topology_changed |= self.reconcile_pid_ambiguity(record.pid);
        }
        if is_member {
            IngestOutcome::Accepted {
                instance_id: id,
                is_start: false,
                topology_changed,
            }
        } else {
            IngestOutcome::Filtered
        }
    }

    fn unique_ambiguous_exit_candidate(
        &self,
        record: &ProcessEtwRecord,
        event_timestamp: Option<i64>,
    ) -> Option<u64> {
        let matches = |process: &TrackedProcess| {
            record.ppid.is_none_or(|ppid| process.ppid == Some(ppid))
                && record
                    .session_id
                    .is_none_or(|session_id| process.session_id == Some(session_id))
                && record.image_file_name.as_ref().is_none_or(|image| {
                    process
                        .image_file_name
                        .as_ref()
                        .is_none_or(|candidate| candidate.eq_ignore_ascii_case(image))
                })
                && event_timestamp.is_none_or(|timestamp| {
                    process
                        .generation_started_at
                        .or(process.first_start_observed_at)
                        .or(process.first_rundown_observed_at)
                        .is_none_or(|started_at| started_at <= timestamp)
                })
        };
        if let Some(witnesses) = self.ambiguous_exit_witnesses.get(&record.pid) {
            if !witnesses.complete {
                return None;
            }
            let mut candidates = witnesses
                .instance_ids
                .iter()
                .filter_map(|id| self.instances.get(id))
                .filter(|process| process.pid == record.pid && matches(process));
            let id = candidates.next()?.id;
            return candidates.next().is_none().then_some(id);
        }
        let mut candidates = self
            .instances
            .values()
            .filter(|process| process.pid == record.pid && matches(process));
        let id = candidates.next()?.id;
        candidates.next().is_none().then_some(id)
    }

    fn link_parent(&mut self, id: u64) {
        let Some(process) = self.instances.get(&id) else {
            return;
        };
        if process.parent_instance.is_some() {
            return;
        }
        let Some(ppid) = process.ppid else {
            self.unknown_parent_count += 1;
            return;
        };
        if ppid == process.pid {
            self.unknown_parent_count += 1;
            return;
        }
        if self.ambiguous_parent_pids.contains_key(&ppid) {
            self.unknown_parent_count += 1;
            return;
        }
        if let Some(parent_id) = self.live_pid_instance.get(&ppid).copied()
            && self.generation_can_own_child(parent_id, id)
        {
            self.attach_child_to_parent(id, parent_id, ppid);
            return;
        }
        if let Some(parent_id) = self.recent_exited_members.get(&ppid).copied() {
            if !self.generation_can_own_child(parent_id, id) {
                self.unknown_parent_count += 1;
                return;
            }
            self.attach_child_to_parent(id, parent_id, ppid);
            return;
        }
        self.unknown_parent_count += 1;
        self.unresolved_by_ppid.entry(ppid).or_default().insert(id);
    }

    fn generation_can_own_child(&self, parent_id: u64, child_id: u64) -> bool {
        let parent_started_at = self
            .instances
            .get(&parent_id)
            .and_then(|parent| parent.generation_started_at);
        let child_started_at = self.instances.get(&child_id).and_then(|child| {
            child
                .generation_started_at
                .or(child.first_start_observed_at)
                .or(child.first_rundown_observed_at)
        });
        !generation_cannot_own_child(parent_started_at, child_started_at)
    }

    fn attach_child_to_parent(&mut self, id: u64, parent_id: u64, ppid: u32) {
        if let Some(process) = self.instances.get_mut(&id) {
            process.parent_instance = Some(parent_id);
        }
        self.unresolved_by_ppid
            .get_mut(&ppid)
            .map(|children| children.remove(&id));
        self.children_by_parent
            .entry(parent_id)
            .or_default()
            .insert(id);
        if self
            .instances
            .get(&parent_id)
            .is_some_and(|process| process.member)
        {
            self.promote_member_subtree(id);
        }
    }

    fn promote_member_subtree(&mut self, root: u64) {
        let mut queue = VecDeque::from([root]);
        let mut seen = HashSet::new();
        while let Some(id) = queue.pop_front() {
            if !seen.insert(id) {
                continue;
            }
            let Some(process) = self.instances.get_mut(&id) else {
                continue;
            };
            process.member = true;
            let pid = process.pid;
            let _ = process;
            self.remove_retained_nonmember_instance(id);
            if !self.ambiguous_parent_pids.contains_key(&pid)
                && let Some(waiting) = self.unresolved_by_ppid.remove(&pid)
            {
                let mut adopted = Vec::new();
                for child in waiting {
                    let child_matches = self.instances.get(&child).is_some_and(|child_process| {
                        child_process.parent_instance.is_none()
                            && child_process.ppid == Some(pid)
                            && child_process.id != id
                    });
                    if !child_matches || !self.generation_can_own_child(id, child) {
                        continue;
                    }
                    if let Some(child_process) = self.instances.get_mut(&child) {
                        child_process.parent_instance = Some(id);
                        adopted.push(child);
                    }
                }
                if !adopted.is_empty() {
                    self.children_by_parent
                        .entry(id)
                        .or_default()
                        .extend(adopted.iter().copied());
                    queue.extend(adopted);
                }
            }
            if let Some(children) = self.children_by_parent.get(&id) {
                queue.extend(children.iter().copied());
            }
        }
        self.enforce_retained_nonmember_instance_limit();
        self.enforce_tracked_instance_limit();
    }

    fn insert_ambiguous_parent_pid(&mut self, pid: u32) {
        if !self.ambiguous_parent_pids.contains_key(&pid) {
            let token = self.next_ambiguity_token;
            self.next_ambiguity_token = self.next_ambiguity_token.wrapping_add(1);
            self.ambiguous_parent_pids.insert(pid, token);
            self.ambiguous_parent_order.push_back((pid, token));
        }
        self.enforce_ambiguous_parent_pid_limit();
    }

    fn mark_sticky_ambiguous_parent_pid(&mut self, pid: u32) {
        self.insert_ambiguous_parent_pid(pid);
        self.sticky_ambiguous_parent_pids.insert(pid);
        let witnesses =
            self.ambiguous_exit_witnesses
                .entry(pid)
                .or_insert_with(|| AmbiguousExitWitnesses {
                    instance_ids: HashSet::new(),
                    complete: true,
                });
        witnesses.instance_ids.extend(
            self.instances
                .values()
                .filter(|process| process.pid == pid)
                .map(|process| process.id),
        );
    }

    fn reconcile_pid_ambiguity(&mut self, pid: u32) -> bool {
        if self.sticky_ambiguous_parent_pids.contains(&pid) {
            return false;
        }
        let live_instances = self.live_pid_counts.get(&pid).copied().unwrap_or(0);
        let surviving_instance = (live_instances == 1).then(|| {
            self.instances
                .values()
                .find(|process| process.pid == pid && !process.seen_exit)
                .map(|process| process.id)
        });
        let mapping_changed = match live_instances {
            0 => self.live_pid_instance.remove(&pid).is_some(),
            1 => match surviving_instance.flatten() {
                Some(id) => self.live_pid_instance.insert(pid, id) != Some(id),
                None => false,
            },
            _ => false,
        };
        let ambiguity_removed =
            live_instances <= 1 && self.ambiguous_parent_pids.remove(&pid).is_some();
        mapping_changed || ambiguity_removed
    }

    fn decrement_live_pid_count(&mut self, pid: u32) {
        let Some(count) = self.live_pid_counts.get_mut(&pid) else {
            return;
        };
        *count = count.saturating_sub(1);
        if *count == 0 {
            self.live_pid_counts.remove(&pid);
        }
    }

    fn enforce_ambiguous_parent_pid_limit(&mut self) {
        while self.ambiguous_parent_order.len() > self.ambiguous_parent_pid_limit {
            let Some((pid, token)) = self.ambiguous_parent_order.pop_front() else {
                break;
            };
            if self.ambiguous_parent_pids.get(&pid) == Some(&token)
                && self.ambiguous_parent_pids.remove(&pid).is_some()
            {
                self.sticky_ambiguous_parent_pids.remove(&pid);
                self.ambiguous_exit_witnesses.remove(&pid);
                self.evicted_ambiguous_parent_count += 1;
            }
        }
    }

    fn retain_recent_exited_member(&mut self, pid: u32, id: u64) {
        self.clear_recent_exited_member(pid);
        self.recent_exited_members.insert(pid, id);
        self.recent_exited_member_order.push_back((pid, id));
        while self.recent_exited_member_order.len() > self.recent_exited_member_limit {
            let Some((old_pid, old_id)) = self.recent_exited_member_order.pop_front() else {
                break;
            };
            if self.recent_exited_members.get(&old_pid) == Some(&old_id) {
                self.recent_exited_members.remove(&old_pid);
            }
        }
    }

    fn clear_recent_exited_member(&mut self, pid: u32) {
        self.recent_exited_members.remove(&pid);
    }

    fn retain_nonmember_instance(&mut self, id: u64) {
        if self.retained_nonmember_ids.insert(id) {
            self.retained_nonmember_order.push_back(id);
        }
    }

    fn remove_retained_nonmember_instance(&mut self, id: u64) {
        self.retained_nonmember_ids.remove(&id);
    }

    fn enforce_retained_nonmember_instance_limit(&mut self) {
        while self.retained_nonmember_order.len() > self.retained_nonmember_instance_limit {
            let Some(id) = self.retained_nonmember_order.pop_front() else {
                break;
            };
            if !self.retained_nonmember_ids.remove(&id) {
                continue;
            }
            if self.remove_instance(id) {
                self.evicted_instance_count += 1;
            }
        }
    }

    fn enforce_tracked_instance_limit(&mut self) {
        while self.instances.len() > self.max_tracked_instances {
            let victim = self
                .instance_order
                .iter()
                .copied()
                .find(|id| {
                    *id != self.root_instance
                        && self
                            .instances
                            .get(id)
                            .is_some_and(|process| !process.member)
                })
                .or_else(|| {
                    self.instance_order.iter().copied().find(|id| {
                        *id != self.root_instance
                            && self
                                .instances
                                .get(id)
                                .is_some_and(|process| process.seen_exit)
                    })
                })
                .or_else(|| {
                    self.instance_order
                        .iter()
                        .copied()
                        .find(|id| *id != self.root_instance && self.instances.contains_key(id))
                });
            let Some(victim) = victim else {
                break;
            };
            let evicted_member_without_exit = self
                .instances
                .get(&victim)
                .is_some_and(|process| process.member && !process.seen_exit);
            if self.remove_instance(victim) {
                self.evicted_instance_count += 1;
                if evicted_member_without_exit {
                    self.evicted_member_instance_count += 1;
                }
            }
        }
    }

    fn remove_instance(&mut self, id: u64) -> bool {
        let Some(process) = self.instances.get(&id).cloned() else {
            return false;
        };
        if process.member
            && !process.seen_exit
            && self
                .children_by_parent
                .get(&id)
                .is_some_and(|children| !children.is_empty())
        {
            self.mark_sticky_ambiguous_parent_pid(process.pid);
        }
        if let Some(witnesses) = self.ambiguous_exit_witnesses.get_mut(&process.pid)
            && witnesses.instance_ids.contains(&id)
        {
            witnesses.complete = false;
        }
        if !process.seen_exit {
            self.decrement_live_pid_count(process.pid);
        }
        self.remove_from_indexes(&process);
        self.instance_order.remove(&id);
        self.instances.remove(&id);
        if let Some(key) = process.unique_process_key
            && self.instances_by_key.get(&key) == Some(&id)
        {
            self.instances_by_key.remove(&key);
        }
        self.reconcile_pid_ambiguity(process.pid);
        self.evicted_instance_ids.push_back(id);
        true
    }

    fn remove_from_indexes(&mut self, process: &TrackedProcess) {
        if let Some(parent) = process.parent_instance
            && let Some(children) = self.children_by_parent.get_mut(&parent)
        {
            children.remove(&process.id);
            if children.is_empty() {
                self.children_by_parent.remove(&parent);
            }
        }
        if let Some(ppid) = process.ppid
            && let Some(children) = self.unresolved_by_ppid.get_mut(&ppid)
        {
            children.remove(&process.id);
            if children.is_empty() {
                self.unresolved_by_ppid.remove(&ppid);
            }
        }
        if let Some(children) = self.children_by_parent.remove(&process.id) {
            for child in children {
                if let Some(child_process) = self.instances.get_mut(&child)
                    && child_process.parent_instance == Some(process.id)
                {
                    child_process.parent_instance = None;
                    if let Some(ppid) = child_process.ppid
                        && !self.ambiguous_parent_pids.contains_key(&ppid)
                    {
                        self.unresolved_by_ppid
                            .entry(ppid)
                            .or_default()
                            .insert(child);
                    }
                }
            }
        }
        if self.live_pid_instance.get(&process.pid) == Some(&process.id) {
            self.live_pid_instance.remove(&process.pid);
        }
        self.remove_retained_nonmember_instance(process.id);
        if self.recent_exited_members.get(&process.pid) == Some(&process.id) {
            self.recent_exited_members.remove(&process.pid);
        }
    }

    fn compact_exited_instances(&mut self) {
        let mut protected = HashSet::from([self.root_instance]);
        for process in self.instances.values().filter(|process| !process.seen_exit) {
            let mut cursor = Some(process.id);
            while let Some(id) = cursor {
                if !protected.insert(id) {
                    break;
                }
                cursor = self
                    .instances
                    .get(&id)
                    .and_then(|tracked| tracked.parent_instance);
            }
        }
        for witnesses in self.ambiguous_exit_witnesses.values() {
            protected.extend(witnesses.instance_ids.iter().copied());
        }

        let removable = self
            .instances
            .iter()
            .filter(|(id, process)| process.seen_exit && !protected.contains(id))
            .map(|(id, _)| *id)
            .collect::<Vec<_>>();
        for id in removable {
            if self.remove_instance(id) {
                self.evicted_instance_count += 1;
            }
        }
        self.exited_since_compaction = 0;
    }

    pub(super) fn stats(&self) -> TrackerStats {
        TrackerStats {
            pid_reuse_count: self.pid_reuse_count,
            unknown_parent_count: self.unknown_parent_count,
            evicted_instance_count: self.evicted_instance_count,
            evicted_ambiguous_parent_count: self.evicted_ambiguous_parent_count,
            evicted_member_instance_count: self.evicted_member_instance_count,
        }
    }

    pub(super) fn take_evicted_instance_ids(&mut self) -> Vec<u64> {
        std::mem::take(&mut self.evicted_instance_ids)
            .into_iter()
            .collect()
    }

    pub(super) fn attribute_pid(&self, pid: u32, event_timestamp: Option<i64>) -> PidAttribution {
        if pid == 0 {
            return PidAttribution::Filtered;
        }
        if self.ambiguous_parent_pids.contains_key(&pid) {
            return PidAttribution::Ambiguous;
        }
        if let Some(id) = self.live_pid_instance.get(&pid).copied()
            && let Some(process) = self.instances.get(&id)
        {
            if generation_cannot_own_child(process.generation_started_at, event_timestamp) {
                return PidAttribution::Filtered;
            }
            if process.member {
                return PidAttribution::Member {
                    instance_id: id,
                    comm: process.image_file_name.clone(),
                };
            }
            if self.has_unresolved_live_ancestor(id) {
                return PidAttribution::Unresolved;
            }
            return PidAttribution::Filtered;
        }
        if let Some(id) = self.recent_exited_members.get(&pid).copied()
            && let Some(process) = self.instances.get(&id)
        {
            if process.member
                && !generation_cannot_own_child(process.generation_started_at, event_timestamp)
            {
                return PidAttribution::Member {
                    instance_id: id,
                    comm: process.image_file_name.clone(),
                };
            }
            return PidAttribution::Filtered;
        }
        PidAttribution::Unresolved
    }

    fn has_unresolved_live_ancestor(&self, start_id: u64) -> bool {
        let mut cursor = Some(start_id);
        let mut visited = 0usize;
        while let Some(id) = cursor {
            if visited >= 64 {
                return false;
            }
            visited += 1;
            let Some(process) = self.instances.get(&id) else {
                return false;
            };
            if process.member {
                return false;
            }
            if process.parent_instance.is_none() {
                return process.first_start_observed_at.is_some();
            }
            cursor = process.parent_instance;
        }
        false
    }
}

fn generation_cannot_own_child(
    parent_started_at: Option<i64>,
    child_started_at: Option<i64>,
) -> bool {
    match (parent_started_at, child_started_at) {
        (Some(_), None) => true,
        (Some(parent_started_at), Some(child_started_at)) => child_started_at < parent_started_at,
        (None, _) => false,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn process_record(pid: u32, ppid: Option<u32>, key: Option<u64>) -> ProcessEtwRecord {
        ProcessEtwRecord {
            pid,
            ppid,
            session_id: Some(1),
            unique_process_key: key,
            image_file_name: Some("process.exe".to_string()),
            command_line: None,
            exit_status: None,
        }
    }

    fn process_exit_record(pid: u32, key: Option<u64>, exit_status: i32) -> ProcessEtwRecord {
        let mut record = process_record(pid, None, key);
        record.exit_status = Some(exit_status);
        record
    }

    #[test]
    fn tracker_follows_descendants_and_pid_reuse() {
        let mut tracker = ProcessTracker::new(100);
        assert!(matches!(
            tracker.ingest(
                process_record(200, Some(100), Some(20)),
                EtwProcessPhase::DCStart
            ),
            IngestOutcome::Accepted { .. }
        ));
        let exit = process_record(200, None, Some(20));
        let IngestOutcome::Accepted {
            instance_id: id, ..
        } = tracker.ingest(exit, EtwProcessPhase::End)
        else {
            panic!("expected tracked child exit");
        };
        let Some(process) = tracker.instances.get(&id) else {
            panic!("expected tracked child instance");
        };
        assert!(process.member);
        assert!(!tracker.live_pid_instance.contains_key(&200));
        assert!(matches!(
            tracker.ingest(
                process_record(200, Some(100), Some(21)),
                EtwProcessPhase::Start,
            ),
            IngestOutcome::Accepted { .. }
        ));
        // The old instance has exited, so the PID map no longer proves that
        // this is reuse. Do not claim stronger evidence than ETW provides.
        assert_eq!(tracker.pid_reuse_count, 0);
    }

    #[test]
    fn reused_unique_process_key_after_exit_creates_a_new_instance() {
        let mut tracker = ProcessTracker::new(100);
        assert!(matches!(
            tracker.ingest(
                process_record(200, Some(100), Some(20)),
                EtwProcessPhase::Start
            ),
            IngestOutcome::Accepted {
                instance_id: first,
                ..
            } if first != tracker.root_instance
        ));
        let first = tracker.instances_by_key[&20];
        assert!(matches!(
            tracker.ingest(process_record(200, None, Some(20)), EtwProcessPhase::End),
            IngestOutcome::Accepted {
                instance_id,
                ..
            } if instance_id == first
        ));
        assert!(tracker.instances[&first].seen_exit);

        let IngestOutcome::Accepted {
            instance_id: second,
            ..
        } = tracker.ingest(
            process_record(200, Some(100), Some(20)),
            EtwProcessPhase::Start,
        )
        else {
            panic!("expected a new instance when the exited key is reused");
        };

        assert_ne!(first, second);
        assert_eq!(tracker.instances_by_key.get(&20), Some(&second));
        assert_eq!(tracker.live_pid_instance.get(&200), Some(&second));
        assert!(tracker.instances[&first].seen_exit);
        assert!(!tracker.instances[&second].seen_exit);
    }

    #[test]
    fn stale_keyless_terminate_does_not_close_a_reused_pid_instance() {
        let mut tracker = ProcessTracker::new(100);
        assert!(matches!(
            tracker.ingest_at(
                process_record(200, Some(100), Some(20)),
                EtwProcessPhase::Start,
                Some(100),
            ),
            IngestOutcome::Accepted { .. }
        ));
        assert!(matches!(
            tracker.ingest_at(
                process_record(200, None, Some(20)),
                EtwProcessPhase::End,
                Some(110),
            ),
            IngestOutcome::Accepted { .. }
        ));
        let IngestOutcome::Accepted {
            instance_id: current,
            ..
        } = tracker.ingest_at(
            process_record(200, Some(100), Some(21)),
            EtwProcessPhase::Start,
            Some(200),
        )
        else {
            panic!("expected the reused PID to start a new instance");
        };

        assert!(matches!(
            tracker.ingest_at(
                process_record(200, None, None),
                EtwProcessPhase::Terminate,
                Some(150),
            ),
            IngestOutcome::Duplicate
        ));
        assert_eq!(tracker.live_pid_instance.get(&200), Some(&current));
        assert!(!tracker.instances[&current].seen_exit);
    }

    #[test]
    fn stale_keyed_end_does_not_close_a_reused_process_key_instance() {
        let mut tracker = ProcessTracker::new(100);
        assert!(matches!(
            tracker.ingest_at(
                process_record(200, Some(100), Some(20)),
                EtwProcessPhase::Start,
                Some(100),
            ),
            IngestOutcome::Accepted { .. }
        ));
        assert!(matches!(
            tracker.ingest_at(
                process_record(200, None, Some(20)),
                EtwProcessPhase::End,
                Some(150),
            ),
            IngestOutcome::Accepted { .. }
        ));
        let IngestOutcome::Accepted {
            instance_id: current,
            ..
        } = tracker.ingest_at(
            process_record(200, Some(100), Some(20)),
            EtwProcessPhase::Start,
            Some(250),
        )
        else {
            panic!("expected a new instance after reusing the process key");
        };

        assert!(matches!(
            tracker.ingest_at(
                process_record(200, None, Some(20)),
                EtwProcessPhase::End,
                Some(150),
            ),
            IngestOutcome::Duplicate
        ));
        assert_eq!(tracker.live_pid_instance.get(&200), Some(&current));
        assert!(!tracker.instances[&current].seen_exit);
    }

    #[test]
    fn initial_child_is_accepted_without_a_full_instance_scan() {
        let mut tracker = ProcessTracker::new(100);
        assert!(matches!(
            tracker.ingest(
                process_record(200, Some(100), Some(21)),
                EtwProcessPhase::Start
            ),
            IngestOutcome::Accepted { .. }
        ));
        assert_eq!(tracker.pid_reuse_count, 0);
    }

    #[test]
    fn late_child_start_is_attributed_to_recently_exited_parent() {
        let mut tracker = ProcessTracker::new(100);
        assert!(matches!(
            tracker.ingest(
                process_record(200, Some(100), Some(20)),
                EtwProcessPhase::Start
            ),
            IngestOutcome::Accepted { .. }
        ));
        assert!(matches!(
            tracker.ingest(process_record(200, None, Some(20)), EtwProcessPhase::End),
            IngestOutcome::Accepted { .. }
        ));
        assert!(matches!(
            tracker.ingest(
                process_record(300, Some(200), Some(30)),
                EtwProcessPhase::Start
            ),
            IngestOutcome::Accepted { .. }
        ));

        let parent_id = tracker.instances_by_key.get(&20).copied().unwrap();
        let child_id = tracker.instances_by_key.get(&30).copied().unwrap();
        assert_eq!(
            tracker
                .instances
                .get(&child_id)
                .and_then(|process| process.parent_instance),
            Some(parent_id)
        );
        assert!(tracker.instances.get(&child_id).is_some_and(|p| p.member));
    }

    #[test]
    fn recent_exited_parent_is_cleared_when_the_pid_starts_again() {
        let mut tracker = ProcessTracker::new(100);
        assert!(matches!(
            tracker.ingest(
                process_record(200, Some(100), Some(20)),
                EtwProcessPhase::Start
            ),
            IngestOutcome::Accepted { .. }
        ));
        assert!(matches!(
            tracker.ingest(process_record(200, None, Some(20)), EtwProcessPhase::End),
            IngestOutcome::Accepted { .. }
        ));
        assert!(matches!(
            tracker.ingest(
                process_record(200, Some(900), Some(21)),
                EtwProcessPhase::Start
            ),
            IngestOutcome::Filtered
        ));
        assert!(matches!(
            tracker.ingest(
                process_record(300, Some(200), Some(30)),
                EtwProcessPhase::Start
            ),
            IngestOutcome::Filtered
        ));

        let child_id = tracker.instances_by_key.get(&30).copied().unwrap();
        let new_parent_id = tracker.instances_by_key.get(&21).copied().unwrap();
        assert_eq!(
            tracker
                .instances
                .get(&child_id)
                .and_then(|process| process.parent_instance),
            Some(new_parent_id)
        );
        assert_ne!(
            tracker
                .instances
                .get(&child_id)
                .and_then(|process| process.parent_instance),
            tracker.instances_by_key.get(&20).copied()
        );
        assert!(!tracker.recent_exited_members.contains_key(&200));
    }

    #[test]
    fn reordered_descendant_tree_is_linked_incrementally() {
        let mut tracker = ProcessTracker::new(100);
        let grandchild = process_record(300, Some(200), Some(30));
        let child = process_record(200, Some(100), Some(20));

        assert!(matches!(
            tracker.ingest(grandchild.clone(), EtwProcessPhase::Start),
            IngestOutcome::Filtered
        ));
        assert!(matches!(
            tracker.ingest(child, EtwProcessPhase::Start),
            IngestOutcome::Accepted { .. }
        ));
        assert!(matches!(
            tracker.ingest(grandchild, EtwProcessPhase::Start),
            IngestOutcome::Accepted { .. }
        ));

        let child_id = tracker.instances_by_key.get(&20).copied().unwrap();
        let grandchild_id = tracker.instances_by_key.get(&30).copied().unwrap();
        assert_eq!(
            tracker
                .instances
                .get(&grandchild_id)
                .and_then(|process| process.parent_instance),
            Some(child_id)
        );
    }

    #[test]
    fn reordered_live_chain_is_promoted_when_its_ancestor_reaches_the_root() {
        let mut tracker = ProcessTracker::new(100);
        let ancestor = process_record(800, Some(100), Some(80));
        let parent = process_record(900, Some(800), Some(90));
        let child = process_record(200, Some(900), Some(20));
        let grandchild = process_record(300, Some(200), Some(30));

        assert!(matches!(
            tracker.ingest(parent.clone(), EtwProcessPhase::Start),
            IngestOutcome::Filtered
        ));
        assert!(matches!(
            tracker.ingest(child.clone(), EtwProcessPhase::Start),
            IngestOutcome::Filtered
        ));
        assert!(matches!(
            tracker.ingest(grandchild.clone(), EtwProcessPhase::Start),
            IngestOutcome::Filtered
        ));

        assert!(matches!(
            tracker.ingest(ancestor, EtwProcessPhase::Start),
            IngestOutcome::Accepted { .. }
        ));
        assert!(matches!(
            tracker.ingest(parent.clone(), EtwProcessPhase::Start),
            IngestOutcome::Accepted { .. }
        ));
        assert!(matches!(
            tracker.ingest(child, EtwProcessPhase::Start),
            IngestOutcome::Accepted { .. }
        ));
        assert!(matches!(
            tracker.ingest(grandchild, EtwProcessPhase::Start),
            IngestOutcome::Accepted { .. }
        ));
    }

    #[test]
    fn pid_reuse_counter_increments_for_a_live_pid() {
        let mut tracker = ProcessTracker::new(100);
        assert!(matches!(
            tracker.ingest(
                process_record(200, Some(100), Some(20)),
                EtwProcessPhase::DCStart,
            ),
            IngestOutcome::Accepted { .. }
        ));
        assert!(matches!(
            tracker.ingest(
                process_record(200, Some(100), Some(21)),
                EtwProcessPhase::Start,
            ),
            IngestOutcome::Accepted { .. }
        ));
        assert_eq!(tracker.pid_reuse_count, 1);
    }

    #[test]
    fn root_pid_reuse_is_not_reattached() {
        let mut tracker = ProcessTracker::new(100);
        assert!(matches!(
            tracker.ingest(process_record(100, None, None), EtwProcessPhase::End),
            IngestOutcome::Accepted {
                instance_id: 0,
                is_start: false,
                ..
            }
        ));
        assert!(matches!(
            tracker.ingest(
                process_record(100, Some(900), Some(99)),
                EtwProcessPhase::Start
            ),
            IngestOutcome::Filtered
        ));
    }

    #[test]
    fn root_pid_reuse_without_key_is_not_bound_to_root() {
        let mut tracker = ProcessTracker::new(100);
        assert!(matches!(
            tracker.ingest(process_record(100, Some(200), None), EtwProcessPhase::Start),
            IngestOutcome::Filtered
        ));
        assert_eq!(tracker.pid_reuse_count, 1);
        assert!(
            tracker
                .instances
                .get(&tracker.root_instance)
                .is_some_and(|process| process.unique_process_key.is_none())
        );
    }

    #[test]
    fn root_pid_reuse_start_with_key_is_not_bound_to_root() {
        let mut tracker = ProcessTracker::new(100);
        assert!(matches!(
            tracker.ingest(
                process_record(100, Some(900), Some(77)),
                EtwProcessPhase::Start
            ),
            IngestOutcome::Filtered
        ));
        assert_eq!(tracker.pid_reuse_count, 1);
        assert!(
            tracker
                .instances
                .get(&tracker.root_instance)
                .is_some_and(|process| process.unique_process_key.is_none())
        );
    }

    #[test]
    fn root_dcstart_binds_unique_process_key() {
        let mut tracker = ProcessTracker::new(100);
        assert!(
            tracker
                .instances
                .get(&tracker.root_instance)
                .and_then(|process| process.unique_process_key)
                .is_none()
        );

        assert!(matches!(
            tracker.ingest(
                process_record(100, None, Some(77)),
                EtwProcessPhase::DCStart
            ),
            IngestOutcome::Accepted {
                instance_id: 0,
                is_start: true,
                ..
            }
        ));
        assert_eq!(tracker.instances_by_key.get(&77), Some(&0));
        assert_eq!(tracker.pid_reuse_count, 0);
    }

    #[test]
    fn legacy_root_dcstart_without_key_still_binds_the_seeded_root() {
        let mut tracker = ProcessTracker::new(100);
        assert!(matches!(
            tracker.ingest(process_record(100, None, None), EtwProcessPhase::DCStart),
            IngestOutcome::Accepted {
                instance_id: 0,
                is_start: true,
                ..
            }
        ));
        assert_eq!(tracker.pid_reuse_count, 0);
    }

    #[test]
    fn process_end_prefers_unique_process_key_over_pid() {
        let mut tracker = ProcessTracker::new(100);
        assert!(matches!(
            tracker.ingest(
                process_record(200, Some(100), Some(20)),
                EtwProcessPhase::DCStart
            ),
            IngestOutcome::Accepted { .. }
        ));

        let exit = ProcessEtwRecord {
            pid: 999,
            ppid: None,
            session_id: None,
            unique_process_key: Some(20),
            image_file_name: None,
            command_line: None,
            exit_status: None,
        };
        assert!(matches!(
            tracker.ingest(exit, EtwProcessPhase::End),
            IngestOutcome::Accepted { .. }
        ));
        assert!(!tracker.live_pid_instance.contains_key(&200));
    }

    #[test]
    fn process_end_with_mismatched_key_does_not_fallback_to_pid() {
        let mut tracker = ProcessTracker::new(100);
        assert!(matches!(
            tracker.ingest(
                process_record(200, Some(100), Some(20)),
                EtwProcessPhase::DCStart
            ),
            IngestOutcome::Accepted { .. }
        ));

        let mismatched = ProcessEtwRecord {
            pid: 200,
            ppid: None,
            session_id: None,
            unique_process_key: Some(21),
            image_file_name: None,
            command_line: None,
            exit_status: None,
        };
        assert!(matches!(
            tracker.ingest(mismatched, EtwProcessPhase::End),
            IngestOutcome::Filtered
        ));
        assert!(tracker.live_pid_instance.contains_key(&200));

        assert!(matches!(
            tracker.ingest(process_record(200, None, Some(20)), EtwProcessPhase::End),
            IngestOutcome::Accepted { .. }
        ));
        assert!(!tracker.live_pid_instance.contains_key(&200));
    }

    #[test]
    fn terminate_after_end_is_a_duplicate_without_entering_pending_replay() {
        let mut tracker = ProcessTracker::new(100);
        assert!(matches!(
            tracker.ingest(
                process_record(200, Some(100), Some(20)),
                EtwProcessPhase::Start
            ),
            IngestOutcome::Accepted { .. }
        ));
        assert!(matches!(
            tracker.ingest(process_record(200, None, Some(20)), EtwProcessPhase::End),
            IngestOutcome::Accepted { .. }
        ));
        assert!(matches!(
            tracker.ingest(process_record(200, None, None), EtwProcessPhase::Terminate),
            IngestOutcome::Duplicate
        ));
    }

    #[test]
    fn terminate_before_end_keeps_the_instance_open_for_authoritative_exit() {
        let mut tracker = ProcessTracker::new(100);
        assert!(matches!(
            tracker.ingest(
                process_record(200, Some(100), Some(20)),
                EtwProcessPhase::Start
            ),
            IngestOutcome::Accepted { .. }
        ));
        let instance_id = tracker.instances_by_key[&20];

        assert!(matches!(
            tracker.ingest(
                process_record(200, None, None),
                EtwProcessPhase::Terminate
            ),
            IngestOutcome::Accepted {
                instance_id: accepted_id,
                is_start: false,
                topology_changed: false,
            } if accepted_id == instance_id
        ));
        let process = tracker.instances.get(&instance_id).unwrap();
        assert!(process.seen_exit);
        assert!(process.terminate_announced);
        assert!(!process.end_announced);
        assert!(!tracker.live_pid_counts.contains_key(&200));

        assert!(matches!(
            tracker.ingest(
                process_exit_record(200, None, 23),
                EtwProcessPhase::End
            ),
            IngestOutcome::Accepted {
                instance_id: accepted_id,
                is_start: false,
                topology_changed: false,
            } if accepted_id == instance_id
        ));
        assert!(tracker.instances[&instance_id].end_announced);
        assert_eq!(tracker.recent_exited_members.get(&200), Some(&instance_id));

        assert!(matches!(
            tracker.ingest(process_exit_record(200, None, 23), EtwProcessPhase::End),
            IngestOutcome::Duplicate
        ));
    }

    #[test]
    fn end_before_terminate_remains_idempotent() {
        let mut tracker = ProcessTracker::new(100);
        assert!(matches!(
            tracker.ingest(
                process_record(200, Some(100), Some(20)),
                EtwProcessPhase::Start
            ),
            IngestOutcome::Accepted { .. }
        ));
        let instance_id = tracker.instances_by_key[&20];

        assert!(matches!(
            tracker.ingest(
                process_exit_record(200, None, -1),
                EtwProcessPhase::End
            ),
            IngestOutcome::Accepted {
                instance_id: accepted_id,
                is_start: false,
                topology_changed: false,
            } if accepted_id == instance_id
        ));
        assert!(tracker.instances[&instance_id].end_announced);
        assert!(!tracker.instances[&instance_id].terminate_announced);

        assert!(matches!(
            tracker.ingest(process_record(200, None, None), EtwProcessPhase::Terminate),
            IngestOutcome::Duplicate
        ));
        assert!(matches!(
            tracker.ingest(process_exit_record(200, None, -1), EtwProcessPhase::End),
            IngestOutcome::Duplicate
        ));
    }

    #[test]
    fn dcend_observes_presence_at_stop_without_finalizing_the_live_instance() {
        let mut tracker = ProcessTracker::new(100);
        assert_eq!(
            EtwProcessPhase::DCEnd.event_name(),
            "PROCESS_PRESENT_AT_STOP"
        );
        assert!(matches!(
            tracker.ingest(
                process_record(200, Some(100), Some(20)),
                EtwProcessPhase::DCStart
            ),
            IngestOutcome::Accepted { .. }
        ));
        let instance_id = tracker.instances_by_key[&20];

        assert!(matches!(
            tracker.ingest(process_record(200, None, None), EtwProcessPhase::DCEnd),
            IngestOutcome::Accepted {
                instance_id: accepted_id,
                is_start: false,
                topology_changed: false,
            } if accepted_id == instance_id
        ));
        let process = &tracker.instances[&instance_id];
        assert!(process.present_at_stop_announced);
        assert!(!process.seen_exit);
        assert_eq!(tracker.live_pid_counts.get(&200), Some(&1));
        assert!(!tracker.recent_exited_members.contains_key(&200));
        assert!(matches!(
            tracker.ingest(process_record(200, None, None), EtwProcessPhase::DCEnd),
            IngestOutcome::Duplicate
        ));

        assert!(matches!(
            tracker.ingest(
                process_exit_record(200, None, 19),
                EtwProcessPhase::End
            ),
            IngestOutcome::Accepted {
                instance_id: accepted_id,
                is_start: false,
                topology_changed: false,
            } if accepted_id == instance_id
        ));
        assert!(tracker.instances[&instance_id].end_announced);
        assert!(!tracker.live_pid_counts.contains_key(&200));
        assert_eq!(tracker.recent_exited_members.get(&200), Some(&instance_id));
    }

    #[test]
    fn keyed_collision_exit_signals_replay_and_restores_the_surviving_parent() {
        let mut tracker = ProcessTracker::new(100);
        assert!(matches!(
            tracker.ingest(
                process_record(200, Some(100), Some(20)),
                EtwProcessPhase::Start
            ),
            IngestOutcome::Accepted { .. }
        ));
        let first_parent = tracker.instances_by_key[&20];
        assert!(matches!(
            tracker.ingest(
                process_record(200, Some(100), Some(21)),
                EtwProcessPhase::Start
            ),
            IngestOutcome::Accepted { .. }
        ));
        let second_parent = tracker.instances_by_key[&21];
        assert!(tracker.ambiguous_parent_pids.contains_key(&200));

        let child = process_record(300, Some(200), Some(30));
        assert!(matches!(
            tracker.ingest(child.clone(), EtwProcessPhase::Start),
            IngestOutcome::Filtered
        ));
        assert!(matches!(
            tracker.ingest(
                process_exit_record(200, Some(21), 0),
                EtwProcessPhase::End
            ),
            IngestOutcome::Accepted {
                instance_id: accepted_id,
                is_start: false,
                topology_changed: true,
            } if accepted_id == second_parent
        ));
        assert!(!tracker.ambiguous_parent_pids.contains_key(&200));
        assert_eq!(tracker.live_pid_counts.get(&200), Some(&1));
        assert_eq!(tracker.live_pid_instance.get(&200), Some(&first_parent));

        assert!(matches!(
            tracker.ingest(child, EtwProcessPhase::Start),
            IngestOutcome::Accepted {
                is_start: true,
                topology_changed: true,
                ..
            }
        ));
        let child = tracker.instances_by_key.get(&30).copied().unwrap();
        assert_eq!(
            tracker.instances[&child].parent_instance,
            Some(first_parent)
        );
        assert!(tracker.instances[&child].member);
    }

    #[test]
    fn ambiguous_keyless_exit_stays_fail_closed_after_another_generation_exits() {
        let mut tracker = ProcessTracker::new(100);
        for key in [20, 21] {
            assert!(matches!(
                tracker.ingest(
                    process_record(200, Some(100), Some(key)),
                    EtwProcessPhase::Start
                ),
                IngestOutcome::Accepted { .. }
            ));
        }
        let first_parent = tracker.instances_by_key[&20];
        let second_parent = tracker.instances_by_key[&21];
        let ambiguous_exit = process_exit_record(200, None, 7);

        assert!(matches!(
            tracker.ingest(ambiguous_exit.clone(), EtwProcessPhase::End),
            IngestOutcome::Filtered
        ));
        assert_eq!(tracker.live_pid_counts.get(&200), Some(&2));
        assert!(!tracker.instances[&first_parent].seen_exit);
        assert!(!tracker.instances[&second_parent].seen_exit);

        assert!(matches!(
            tracker.ingest(
                process_exit_record(200, Some(21), 0),
                EtwProcessPhase::End
            ),
            IngestOutcome::Accepted {
                instance_id: accepted_id,
                topology_changed: false,
                ..
            } if accepted_id == second_parent
        ));
        assert_eq!(tracker.live_pid_instance.get(&200), None);
        assert!(tracker.ambiguous_parent_pids.contains_key(&200));

        // A keyed exit of the other generation does not prove which keyless
        // exit record belongs to the survivor. Keep it fail-closed.
        assert!(matches!(
            tracker.ingest(ambiguous_exit, EtwProcessPhase::End),
            IngestOutcome::Filtered
        ));
        assert!(!tracker.instances[&first_parent].seen_exit);
        assert!(!tracker.instances[&first_parent].end_announced);
        assert_eq!(tracker.live_pid_counts.get(&200), Some(&1));
    }

    #[test]
    fn ambiguous_keyless_terminate_remains_unresolved_after_keyed_exit() {
        let mut tracker = ProcessTracker::new(100);
        for key in [20, 21] {
            assert!(matches!(
                tracker.ingest(
                    process_record(200, Some(100), Some(key)),
                    EtwProcessPhase::Start
                ),
                IngestOutcome::Accepted { .. }
            ));
        }
        let first_parent = tracker.instances_by_key[&20];
        let second_parent = tracker.instances_by_key[&21];

        assert!(matches!(
            tracker.ingest(process_record(200, None, None), EtwProcessPhase::Terminate),
            IngestOutcome::Filtered
        ));
        assert_eq!(tracker.live_pid_counts.get(&200), Some(&2));
        assert!(!tracker.instances[&first_parent].terminate_announced);
        assert!(!tracker.instances[&second_parent].terminate_announced);

        assert!(matches!(
            tracker.ingest(process_exit_record(200, Some(21), 0), EtwProcessPhase::End),
            IngestOutcome::Accepted {
                topology_changed: false,
                ..
            }
        ));
        assert!(matches!(
            tracker.ingest(process_record(200, None, None), EtwProcessPhase::Terminate),
            IngestOutcome::Filtered
        ));
        assert!(!tracker.instances[&first_parent].terminate_announced);

        assert!(matches!(
            tracker.ingest(process_exit_record(200, None, 9), EtwProcessPhase::End),
            IngestOutcome::Filtered
        ));
        assert!(!tracker.instances[&first_parent].end_announced);
        assert_eq!(tracker.live_pid_counts.get(&200), Some(&1));
    }

    #[test]
    fn ambiguous_keyless_exit_keeps_its_original_candidate_witnesses() {
        let mut tracker = ProcessTracker::new(100);
        for key in [20, 21] {
            assert!(matches!(
                tracker.ingest(
                    process_record(200, Some(100), Some(key)),
                    EtwProcessPhase::Start
                ),
                IngestOutcome::Accepted { .. }
            ));
        }
        let survivor = tracker.instances_by_key[&20];
        let exiting = tracker.instances_by_key[&21];
        let ambiguous_exit = process_exit_record(200, None, 7);

        assert!(matches!(
            tracker.ingest(ambiguous_exit.clone(), EtwProcessPhase::End),
            IngestOutcome::Filtered
        ));
        assert!(matches!(
            tracker.ingest(process_exit_record(200, Some(21), 0), EtwProcessPhase::End),
            IngestOutcome::Accepted { .. }
        ));
        assert_eq!(
            tracker.ambiguous_exit_witnesses[&200].instance_ids,
            HashSet::from([survivor, exiting])
        );

        tracker.compact_exited_instances();
        assert!(
            tracker.instances.contains_key(&exiting),
            "ambiguity witnesses must survive ordinary cache compaction"
        );
        assert!(matches!(
            tracker.ingest(ambiguous_exit.clone(), EtwProcessPhase::End),
            IngestOutcome::Filtered
        ));

        assert!(tracker.remove_instance(exiting));
        assert!(!tracker.ambiguous_exit_witnesses[&200].complete);
        assert!(
            matches!(
                tracker.ingest(ambiguous_exit, EtwProcessPhase::End),
                IngestOutcome::Filtered
            ),
            "losing a candidate must fail closed even when one live instance remains"
        );
        assert_eq!(tracker.live_pid_counts.get(&200), Some(&1));
        assert!(!tracker.instances[&survivor].seen_exit);
    }

    #[test]
    fn nonmember_keyless_terminate_can_replay_after_its_parent_promotes_it() {
        let mut tracker = ProcessTracker::new(100);
        assert!(matches!(
            tracker.ingest(
                process_record(200, Some(150), Some(20)),
                EtwProcessPhase::Start
            ),
            IngestOutcome::Filtered
        ));
        let child = tracker.instances_by_key[&20];
        assert!(!tracker.instances[&child].member);

        assert!(matches!(
            tracker.ingest(process_record(200, None, None), EtwProcessPhase::Terminate),
            IngestOutcome::Filtered
        ));
        assert!(!tracker.instances[&child].seen_exit);
        assert!(!tracker.instances[&child].terminate_announced);
        assert_eq!(tracker.live_pid_instance.get(&200), Some(&child));
        assert_eq!(tracker.live_pid_counts.get(&200), Some(&1));

        assert!(matches!(
            tracker.ingest(
                process_record(150, Some(100), Some(15)),
                EtwProcessPhase::Start
            ),
            IngestOutcome::Accepted {
                is_start: true,
                topology_changed: true,
                ..
            }
        ));
        assert!(tracker.instances[&child].member);

        assert!(matches!(
            tracker.ingest(
                process_record(200, None, None),
                EtwProcessPhase::Terminate
            ),
            IngestOutcome::Accepted {
                instance_id,
                is_start: false,
                ..
            } if instance_id == child
        ));
        assert!(tracker.instances[&child].seen_exit);
        assert!(tracker.instances[&child].terminate_announced);
        assert!(!tracker.instances[&child].end_announced);
        assert_eq!(tracker.recent_exited_members.get(&200), Some(&child));
        assert!(matches!(
            tracker.ingest(process_record(200, None, None), EtwProcessPhase::Terminate),
            IngestOutcome::Duplicate
        ));
    }

    #[test]
    fn ambiguous_keyless_exit_resolves_only_from_unique_instance_evidence() {
        let mut tracker = ProcessTracker::new(100);
        let mut first = process_record(200, Some(100), Some(20));
        first.image_file_name = Some("first.exe".to_string());
        assert!(matches!(
            tracker.ingest(first, EtwProcessPhase::Start),
            IngestOutcome::Accepted { .. }
        ));
        let first_parent = tracker.instances_by_key[&20];

        let mut second = process_record(200, Some(100), Some(21));
        second.image_file_name = Some("second.exe".to_string());
        assert!(matches!(
            tracker.ingest(second, EtwProcessPhase::Start),
            IngestOutcome::Accepted { .. }
        ));
        assert!(tracker.ambiguous_parent_pids.contains_key(&200));

        let mut exit = process_exit_record(200, None, 7);
        exit.image_file_name = Some("first.exe".to_string());
        assert!(matches!(
            tracker.ingest(exit, EtwProcessPhase::End),
            IngestOutcome::Accepted {
                instance_id,
                is_start: false,
                ..
            } if instance_id == first_parent
        ));
        assert!(tracker.instances[&first_parent].end_announced);
        assert_eq!(tracker.live_pid_counts.get(&200), Some(&1));
    }

    #[test]
    fn unrelated_and_duplicate_events_are_not_decode_errors() {
        let mut tracker = ProcessTracker::new(100);
        assert!(matches!(
            tracker.ingest(
                process_record(200, Some(999), Some(20)),
                EtwProcessPhase::Start
            ),
            IngestOutcome::Filtered
        ));
        assert!(matches!(
            tracker.ingest(
                process_record(300, Some(100), Some(30)),
                EtwProcessPhase::DCStart
            ),
            IngestOutcome::Accepted { .. }
        ));
        assert!(matches!(
            tracker.ingest(
                process_record(300, Some(100), Some(30)),
                EtwProcessPhase::Start
            ),
            IngestOutcome::Duplicate
        ));
    }

    #[test]
    fn deferred_descendant_is_accepted_after_a_reordered_parent_start() {
        let mut tracker = ProcessTracker::new(100);
        assert!(matches!(
            tracker.ingest(
                process_record(300, Some(200), Some(30)),
                EtwProcessPhase::Start
            ),
            IngestOutcome::Filtered
        ));
        assert!(matches!(
            tracker.ingest(
                process_record(200, Some(100), Some(20)),
                EtwProcessPhase::Start
            ),
            IngestOutcome::Accepted { .. }
        ));
        assert!(matches!(
            tracker.ingest(
                process_record(300, Some(200), Some(30)),
                EtwProcessPhase::Start
            ),
            IngestOutcome::Accepted { .. }
        ));
        assert!(matches!(
            tracker.ingest(
                process_record(300, Some(200), Some(30)),
                EtwProcessPhase::Start
            ),
            IngestOutcome::Duplicate
        ));
    }

    #[test]
    fn parent_pid_reuse_does_not_reattach_a_child_to_the_old_parent() {
        let mut tracker = ProcessTracker::new(100);
        assert!(matches!(
            tracker.ingest(
                process_record(200, Some(100), Some(20)),
                EtwProcessPhase::DCStart
            ),
            IngestOutcome::Accepted { .. }
        ));
        assert!(matches!(
            tracker.ingest(process_record(200, None, Some(20)), EtwProcessPhase::End),
            IngestOutcome::Accepted { .. }
        ));
        assert!(matches!(
            tracker.ingest(
                process_record(200, Some(900), Some(21)),
                EtwProcessPhase::Start
            ),
            IngestOutcome::Filtered
        ));
        assert!(matches!(
            tracker.ingest(
                process_record(300, Some(200), Some(30)),
                EtwProcessPhase::Start
            ),
            IngestOutcome::Filtered
        ));
        let child = tracker
            .instances
            .values()
            .find(|process| process.pid == 300)
            .expect("child instance is retained for attribution");
        assert_eq!(
            child.parent_instance,
            tracker.instances_by_key.get(&21).copied()
        );
        assert_ne!(
            child.parent_instance,
            tracker.instances_by_key.get(&20).copied()
        );
        assert_eq!(tracker.unknown_parent_count, 1);
    }

    #[test]
    fn exited_unrelated_instances_are_compacted() {
        let mut tracker = ProcessTracker::new(100);
        for offset in 0..TRACKER_COMPACTION_INTERVAL {
            let pid = 1_000 + offset as u32;
            let key = 10_000 + offset;
            tracker.ingest(
                process_record(pid, Some(999), Some(key)),
                EtwProcessPhase::Start,
            );
            tracker.ingest(process_record(pid, None, Some(key)), EtwProcessPhase::End);
        }

        assert_eq!(tracker.evicted_instance_count, TRACKER_COMPACTION_INTERVAL);
        assert_eq!(tracker.instances.len(), 1);
        assert!(tracker.instances.contains_key(&tracker.root_instance));
        assert!(tracker.children_by_parent.is_empty());
        assert!(tracker.unresolved_by_ppid.is_empty());
    }

    #[test]
    fn sustained_missing_exits_retain_a_bounded_number_of_unresolved_instances() {
        const RETAINED_LIMIT: usize = 4;
        let mut tracker = ProcessTracker::new_with_limits(100, 8, RETAINED_LIMIT, 8, 64);
        for offset in 0..20 {
            let pid = 1_000 + offset;
            let key = 10_000 + u64::from(offset);
            tracker.ingest(
                process_record(pid, Some(999), Some(key)),
                EtwProcessPhase::Start,
            );
        }

        let stats = tracker.stats();
        assert_eq!(stats.evicted_instance_count, 16);
        assert_eq!(tracker.instances.len(), RETAINED_LIMIT + 1);
        assert_eq!(tracker.retained_nonmember_order.len(), RETAINED_LIMIT);
        assert_eq!(tracker.instance_order.len(), RETAINED_LIMIT + 1);
        assert_eq!(
            tracker.instances_by_key.len(),
            RETAINED_LIMIT,
            "evicted unique-process keys must be removed"
        );
        assert_eq!(
            tracker.live_pid_instance.len(),
            RETAINED_LIMIT + 1,
            "only retained instances and the root keep live-PID mappings"
        );
        assert!(
            tracker
                .unresolved_by_ppid
                .values()
                .all(|children| children.iter().all(|id| tracker.instances.contains_key(id))),
            "evicted unresolved children must be removed from every PID set"
        );
        assert!(
            tracker
                .unresolved_by_ppid
                .get(&999)
                .is_some_and(|children| children.len() == RETAINED_LIMIT)
        );
    }

    #[test]
    fn ambiguous_parent_pids_are_bounded_and_counted() {
        let mut tracker = ProcessTracker::new_with_limits(100, 8, 8, 2, 64);
        for pid in [200, 201, 202] {
            assert!(matches!(
                tracker.ingest(
                    process_record(pid, Some(100), Some(u64::from(pid))),
                    EtwProcessPhase::Start
                ),
                IngestOutcome::Accepted { .. }
            ));
            assert!(matches!(
                tracker.ingest(
                    process_record(pid, Some(100), Some(u64::from(pid) + 100)),
                    EtwProcessPhase::Start
                ),
                IngestOutcome::Accepted { .. }
            ));
        }

        assert!(!tracker.ambiguous_parent_pids.contains_key(&200));
        assert!(tracker.ambiguous_parent_pids.contains_key(&201));
        assert!(tracker.ambiguous_parent_pids.contains_key(&202));
        assert_eq!(tracker.ambiguous_parent_order.len(), 2);
        assert_eq!(tracker.stats().evicted_ambiguous_parent_count, 1);
    }

    #[test]
    fn stale_ambiguity_tokens_cannot_remove_a_new_collision_for_the_same_pid() {
        let mut tracker = ProcessTracker::new_with_limits(100, 8, 16, 2, 64);

        for key in [20, 21] {
            assert!(matches!(
                tracker.ingest(
                    process_record(200, Some(100), Some(key)),
                    EtwProcessPhase::Start
                ),
                IngestOutcome::Accepted { .. }
            ));
        }
        for key in [20, 21] {
            assert!(matches!(
                tracker.ingest(process_record(200, None, Some(key)), EtwProcessPhase::End),
                IngestOutcome::Accepted { .. }
            ));
        }
        assert!(!tracker.ambiguous_parent_pids.contains_key(&200));

        for key in [30, 31] {
            tracker.ingest(
                process_record(201, Some(100), Some(key)),
                EtwProcessPhase::Start,
            );
        }
        for key in [22, 23] {
            tracker.ingest(
                process_record(200, Some(100), Some(key)),
                EtwProcessPhase::Start,
            );
        }

        assert!(tracker.ambiguous_parent_pids.contains_key(&200));
        assert!(tracker.ambiguous_parent_pids.contains_key(&201));
        assert_eq!(tracker.ambiguous_parent_order.len(), 2);
        assert_eq!(tracker.stats().evicted_ambiguous_parent_count, 0);
    }

    #[test]
    fn capacity_eviction_clears_collision_ambiguity_when_no_live_generation_remains() {
        const MAX_INSTANCES: usize = 5;
        let mut tracker = ProcessTracker::new_with_limits(100, 8, 64, 8, MAX_INSTANCES);
        for key in [20, 21] {
            assert!(matches!(
                tracker.ingest(
                    process_record(200, Some(100), Some(key)),
                    EtwProcessPhase::Start
                ),
                IngestOutcome::Accepted { .. }
            ));
        }
        assert!(tracker.ambiguous_parent_pids.contains_key(&200));

        for offset in 0..4 {
            let pid = 1_000 + offset;
            let key = 1_000 + u64::from(offset);
            assert!(matches!(
                tracker.ingest(
                    process_record(pid, Some(100), Some(key)),
                    EtwProcessPhase::Start
                ),
                IngestOutcome::Accepted { .. }
            ));
        }

        assert!(tracker.instances.values().all(|process| process.pid != 200));
        assert!(!tracker.ambiguous_parent_pids.contains_key(&200));

        assert!(matches!(
            tracker.ingest(
                process_record(200, Some(100), Some(22)),
                EtwProcessPhase::Start
            ),
            IngestOutcome::Accepted { .. }
        ));
        assert!(matches!(
            tracker.ingest(
                process_record(300, Some(200), Some(30)),
                EtwProcessPhase::Start
            ),
            IngestOutcome::Accepted { .. }
        ));
        let new_parent_id = tracker.instances_by_key.get(&22).copied().unwrap();
        let child = tracker
            .instances
            .values()
            .find(|process| process.pid == 300)
            .expect("child of the new, unambiguous PID generation");
        assert_eq!(child.parent_instance, Some(new_parent_id));
        assert!(child.member);
    }

    #[test]
    fn late_child_of_an_evicted_collision_generation_is_not_attached_to_the_live_generation() {
        let mut tracker = ProcessTracker::new(100);
        assert!(matches!(
            tracker.ingest_at(
                process_record(200, Some(100), Some(20)),
                EtwProcessPhase::Start,
                Some(100),
            ),
            IngestOutcome::Accepted { .. }
        ));
        let first_generation = tracker.instances_by_key.get(&20).copied().unwrap();
        assert!(matches!(
            tracker.ingest_at(
                process_record(200, Some(100), Some(21)),
                EtwProcessPhase::Start,
                Some(200),
            ),
            IngestOutcome::Accepted { .. }
        ));
        assert!(tracker.ambiguous_parent_pids.contains_key(&200));

        assert!(tracker.remove_instance(first_generation));
        assert_eq!(tracker.live_pid_counts.get(&200), Some(&1));
        assert!(!tracker.ambiguous_parent_pids.contains_key(&200));

        let late_child = process_record(300, Some(200), Some(30));
        assert!(matches!(
            tracker.ingest_at(late_child.clone(), EtwProcessPhase::Start, Some(150)),
            IngestOutcome::Filtered
        ));
        assert!(matches!(
            tracker.ingest_at(late_child, EtwProcessPhase::Start, Some(150)),
            IngestOutcome::Filtered
        ));
        let child = tracker.instances_by_key.get(&30).copied().unwrap();
        let child = tracker.instances.get(&child).unwrap();
        assert_eq!(child.parent_instance, None);
        assert!(!child.member);
    }

    #[test]
    fn replayed_old_generation_child_is_not_adopted_when_its_pid_generation_starts() {
        let mut tracker = ProcessTracker::new(100);
        assert!(matches!(
            tracker.ingest_at(
                process_record(200, Some(100), Some(20)),
                EtwProcessPhase::Start,
                Some(100),
            ),
            IngestOutcome::Accepted { .. }
        ));
        let first_generation = tracker.instances_by_key.get(&20).copied().unwrap();
        assert!(tracker.remove_instance(first_generation));

        assert!(matches!(
            tracker.ingest_at(
                process_record(300, Some(200), Some(30)),
                EtwProcessPhase::Start,
                Some(150),
            ),
            IngestOutcome::Filtered
        ));
        assert!(matches!(
            tracker.ingest_at(
                process_record(200, Some(100), Some(21)),
                EtwProcessPhase::Start,
                Some(200),
            ),
            IngestOutcome::Accepted { .. }
        ));

        let child = tracker.instances_by_key.get(&30).copied().unwrap();
        let child = tracker.instances.get(&child).unwrap();
        assert_eq!(child.parent_instance, None);
        assert!(!child.member);
    }

    #[test]
    fn evicting_an_active_parent_is_fail_closed_for_reused_pid_child_attribution() {
        let mut tracker = ProcessTracker::new(100);
        assert!(matches!(
            tracker.ingest(
                process_record(200, Some(100), Some(20)),
                EtwProcessPhase::Start
            ),
            IngestOutcome::Accepted { .. }
        ));
        assert!(matches!(
            tracker.ingest(
                process_record(300, Some(200), Some(30)),
                EtwProcessPhase::Start
            ),
            IngestOutcome::Accepted { .. }
        ));
        let parent_id = tracker.instances_by_key.get(&20).copied().unwrap();
        let child_id = tracker.instances_by_key.get(&30).copied().unwrap();

        assert!(tracker.remove_instance(parent_id));
        assert!(tracker.ambiguous_parent_pids.contains_key(&200));
        assert!(tracker.sticky_ambiguous_parent_pids.contains(&200));
        assert!(!tracker.unresolved_by_ppid.contains_key(&200));
        assert_eq!(
            tracker
                .instances
                .get(&child_id)
                .and_then(|process| process.parent_instance),
            None
        );

        assert!(matches!(
            tracker.ingest(
                process_record(200, Some(100), Some(21)),
                EtwProcessPhase::Start
            ),
            IngestOutcome::Accepted { .. }
        ));
        assert!(matches!(
            tracker.ingest(
                process_record(400, Some(200), Some(40)),
                EtwProcessPhase::Start
            ),
            IngestOutcome::Filtered
        ));
        let reused_pid_child = tracker
            .instances
            .values()
            .find(|process| process.pid == 400)
            .expect("child awaiting an unambiguous parent generation");
        assert_eq!(reused_pid_child.parent_instance, None);
        assert!(!reused_pid_child.member);
    }

    #[test]
    fn missing_exit_member_churn_is_globally_bounded() {
        const MAX_INSTANCES: usize = 8;
        let mut tracker = ProcessTracker::new_with_limits(100, 8, 64, 8, MAX_INSTANCES);
        for offset in 0..20 {
            let pid = 1_000 + offset;
            let key = 10_000 + u64::from(offset);
            assert!(matches!(
                tracker.ingest(
                    process_record(pid, Some(100), Some(key)),
                    EtwProcessPhase::Start
                ),
                IngestOutcome::Accepted { .. }
            ));
        }

        let stats = tracker.stats();
        assert!(tracker.instances.len() <= MAX_INSTANCES);
        assert!(tracker.instances.contains_key(&tracker.root_instance));
        assert_eq!(stats.evicted_member_instance_count, 13);
        assert_eq!(stats.evicted_instance_count, 13);
        assert_eq!(tracker.take_evicted_instance_ids().len(), 13);
    }

    #[test]
    fn pid_reuse_ambiguity_clears_when_the_live_generation_exits() {
        let mut tracker = ProcessTracker::new(100);
        assert!(matches!(
            tracker.ingest(
                process_record(200, Some(100), Some(20)),
                EtwProcessPhase::Start
            ),
            IngestOutcome::Accepted { .. }
        ));
        assert!(matches!(
            tracker.ingest(
                process_record(200, Some(100), Some(21)),
                EtwProcessPhase::Start
            ),
            IngestOutcome::Accepted { .. }
        ));
        assert!(tracker.ambiguous_parent_pids.contains_key(&200));

        assert!(matches!(
            tracker.ingest(process_record(200, None, Some(20)), EtwProcessPhase::End),
            IngestOutcome::Accepted { .. }
        ));
        assert!(matches!(
            tracker.ingest(process_record(200, None, Some(21)), EtwProcessPhase::End),
            IngestOutcome::Accepted { .. }
        ));
        assert!(!tracker.ambiguous_parent_pids.contains_key(&200));

        assert!(matches!(
            tracker.ingest(
                process_record(200, Some(100), Some(22)),
                EtwProcessPhase::Start
            ),
            IngestOutcome::Accepted { .. }
        ));
        assert!(matches!(
            tracker.ingest(
                process_record(300, Some(200), Some(30)),
                EtwProcessPhase::Start
            ),
            IngestOutcome::Accepted { .. }
        ));
        let child = tracker
            .instances
            .values()
            .find(|process| process.pid == 300)
            .expect("third-generation child");
        assert!(child.parent_instance.is_some());
    }

    #[test]
    fn live_pid_counts_track_starts_exits_and_duplicate_events_without_drift() {
        let mut tracker = ProcessTracker::new(100);
        assert!(matches!(
            tracker.ingest(
                process_record(200, Some(100), Some(20)),
                EtwProcessPhase::DCStart
            ),
            IngestOutcome::Accepted { .. }
        ));
        assert_eq!(tracker.live_pid_counts.get(&200), Some(&1));
        assert!(matches!(
            tracker.ingest(
                process_record(200, Some(100), Some(20)),
                EtwProcessPhase::Start
            ),
            IngestOutcome::Duplicate
        ));
        assert_eq!(tracker.live_pid_counts.get(&200), Some(&1));

        assert!(matches!(
            tracker.ingest(process_record(200, None, Some(20)), EtwProcessPhase::End),
            IngestOutcome::Accepted { .. }
        ));
        assert!(!tracker.live_pid_counts.contains_key(&200));
        assert!(matches!(
            tracker.ingest(process_record(200, None, Some(20)), EtwProcessPhase::End),
            IngestOutcome::Duplicate
        ));
        assert!(!tracker.live_pid_counts.contains_key(&200));
    }

    #[test]
    fn recent_exited_parent_generation_rejects_an_older_late_child() {
        let mut tracker = ProcessTracker::new(100);
        assert!(matches!(
            tracker.ingest_at(
                process_record(200, Some(100), Some(20)),
                EtwProcessPhase::Start,
                Some(100),
            ),
            IngestOutcome::Accepted { .. }
        ));
        assert!(matches!(
            tracker.ingest(process_record(200, None, Some(20)), EtwProcessPhase::End),
            IngestOutcome::Accepted { .. }
        ));
        assert!(matches!(
            tracker.ingest_at(
                process_record(200, Some(100), Some(21)),
                EtwProcessPhase::Start,
                Some(200),
            ),
            IngestOutcome::Accepted { .. }
        ));
        assert!(matches!(
            tracker.ingest(process_record(200, None, Some(21)), EtwProcessPhase::End),
            IngestOutcome::Accepted { .. }
        ));

        assert!(matches!(
            tracker.ingest_at(
                process_record(300, Some(200), Some(30)),
                EtwProcessPhase::Start,
                Some(150),
            ),
            IngestOutcome::Filtered
        ));
        let child = tracker.instances_by_key.get(&30).copied().unwrap();
        let child = tracker.instances.get(&child).unwrap();
        assert_eq!(child.parent_instance, None);
        assert!(!child.member);
    }

    #[test]
    fn overlapping_rundown_and_live_start_retains_start_boundary() {
        let mut tracker = ProcessTracker::new(100);
        assert!(matches!(
            tracker.ingest_at(
                process_record(200, Some(100), Some(20)),
                EtwProcessPhase::DCStart,
                Some(100),
            ),
            IngestOutcome::Accepted { .. }
        ));
        assert!(matches!(
            tracker.ingest_at(
                process_record(200, Some(100), Some(20)),
                EtwProcessPhase::Start,
                Some(105),
            ),
            IngestOutcome::Duplicate
        ));

        let process = tracker
            .instances
            .get(&tracker.instances_by_key[&20])
            .unwrap();
        assert_eq!(process.first_rundown_observed_at, Some(100));
        assert_eq!(process.first_start_observed_at, Some(105));
        assert_eq!(process.generation_started_at, Some(105));
    }

    #[test]
    fn dcstart_child_is_not_adopted_by_a_reused_pid_generation() {
        let mut tracker = ProcessTracker::new(100);
        assert!(matches!(
            tracker.ingest_at(
                process_record(200, Some(100), Some(20)),
                EtwProcessPhase::DCStart,
                Some(100),
            ),
            IngestOutcome::Accepted { .. }
        ));
        let old_parent = tracker.instances_by_key.get(&20).copied().unwrap();
        assert!(tracker.remove_instance(old_parent));

        assert!(matches!(
            tracker.ingest_at(
                process_record(300, Some(200), Some(30)),
                EtwProcessPhase::DCStart,
                Some(100),
            ),
            IngestOutcome::Filtered
        ));
        assert!(matches!(
            tracker.ingest_at(
                process_record(200, Some(100), Some(21)),
                EtwProcessPhase::Start,
                Some(200),
            ),
            IngestOutcome::Accepted { .. }
        ));

        let child = tracker.instances_by_key.get(&30).copied().unwrap();
        let child = tracker.instances.get(&child).unwrap();
        assert_eq!(child.first_rundown_observed_at, Some(100));
        assert_eq!(child.parent_instance, None);
        assert!(!child.member);
    }

    #[test]
    fn replayed_keyless_deferred_start_is_idempotent() {
        let mut tracker = ProcessTracker::new(100);
        let child = process_record(300, Some(200), None);
        for _ in 0..2 {
            assert!(matches!(
                tracker.ingest_at(child.clone(), EtwProcessPhase::Start, Some(150)),
                IngestOutcome::Filtered
            ));
        }

        assert_eq!(tracker.pid_reuse_count, 0);
        assert_eq!(
            tracker
                .instances
                .values()
                .filter(|process| process.pid == 300)
                .count(),
            1
        );
        assert_eq!(tracker.live_pid_counts.get(&300), Some(&1));
        let child_id = tracker
            .instances
            .values()
            .find(|process| process.pid == 300)
            .unwrap()
            .id;

        assert!(matches!(
            tracker.ingest_at(
                process_record(200, Some(100), Some(20)),
                EtwProcessPhase::Start,
                Some(100),
            ),
            IngestOutcome::Accepted { .. }
        ));
        assert!(matches!(
            tracker.ingest_at(child, EtwProcessPhase::Start, Some(150)),
            IngestOutcome::Accepted {
                instance_id,
                is_start: true,
                ..
            } if instance_id == child_id
        ));
        assert_eq!(
            tracker
                .instances
                .values()
                .filter(|process| process.pid == 300)
                .count(),
            1
        );
        assert_eq!(tracker.live_pid_counts.get(&300), Some(&1));
    }

    #[test]
    fn keyless_rundown_then_live_start_is_one_generation() {
        let mut tracker = ProcessTracker::new(100);
        assert!(matches!(
            tracker.ingest_at(
                process_record(300, Some(100), None),
                EtwProcessPhase::DCStart,
                Some(100),
            ),
            IngestOutcome::Accepted { .. }
        ));
        assert!(matches!(
            tracker.ingest_at(
                process_record(300, Some(100), None),
                EtwProcessPhase::Start,
                Some(105),
            ),
            IngestOutcome::Duplicate
        ));

        assert_eq!(
            tracker
                .instances
                .values()
                .filter(|process| process.pid == 300)
                .count(),
            1
        );
        assert_eq!(tracker.live_pid_counts.get(&300), Some(&1));
        assert!(!tracker.ambiguous_parent_pids.contains_key(&300));
        let process = tracker
            .instances
            .values()
            .find(|process| process.pid == 300)
            .unwrap();
        assert_eq!(process.first_rundown_observed_at, Some(100));
        assert_eq!(process.first_start_observed_at, Some(105));
        assert_eq!(process.generation_started_at, Some(105));

        assert!(matches!(
            tracker.ingest_at(
                process_record(300, Some(100), None),
                EtwProcessPhase::Start,
                Some(200),
            ),
            IngestOutcome::Accepted { .. }
        ));
        assert_eq!(tracker.live_pid_counts.get(&300), Some(&2));
        assert!(tracker.ambiguous_parent_pids.contains_key(&300));
    }

    #[test]
    fn attribute_pid_handles_members_rundown_nonmembers_deferrals_and_ambiguity() {
        let mut tracker = ProcessTracker::new(100);
        assert_eq!(tracker.attribute_pid(0, Some(100)), PidAttribution::Filtered);
        assert_eq!(
            tracker.attribute_pid(100, Some(100)),
            PidAttribution::Member {
                instance_id: tracker.root_instance,
                comm: None,
            }
        );

        // Pre-existing host DCStart non-member is filtered immediately without deferral.
        assert_eq!(
            tracker.ingest_at(
                process_record(500, Some(1), Some(50)),
                EtwProcessPhase::DCStart,
                Some(90),
            ),
            IngestOutcome::Filtered
        );
        assert_eq!(tracker.attribute_pid(500, Some(95)), PidAttribution::Filtered);

        // Unseen PID and newly started live unresolved child are deferred until promotion.
        assert_eq!(
            tracker.attribute_pid(200, Some(100)),
            PidAttribution::Unresolved
        );
        assert_eq!(
            tracker.ingest_at(
                process_record(300, Some(200), Some(30)),
                EtwProcessPhase::Start,
                Some(120),
            ),
            IngestOutcome::Filtered
        );
        assert_eq!(
            tracker.attribute_pid(300, Some(125)),
            PidAttribution::Unresolved
        );

        assert!(matches!(
            tracker.ingest_at(
                process_record(200, Some(100), Some(20)),
                EtwProcessPhase::Start,
                Some(100),
            ),
            IngestOutcome::Accepted {
                topology_changed: true,
                ..
            }
        ));
        let child_id = tracker.live_pid_instance[&300];
        assert_eq!(
            tracker.attribute_pid(300, Some(125)),
            PidAttribution::Member {
                instance_id: child_id,
                comm: Some("process.exe".to_string()),
            }
        );

        // Events predating current generation_started_at or lacking timestamp fail closed.
        assert_eq!(
            tracker.attribute_pid(300, Some(119)),
            PidAttribution::Filtered
        );
        assert_eq!(tracker.attribute_pid(300, None), PidAttribution::Filtered);

        // Recent exited member stays attributable until PID is reused.
        assert!(matches!(
            tracker.ingest_at(
                process_exit_record(300, Some(30), 0),
                EtwProcessPhase::End,
                Some(140),
            ),
            IngestOutcome::Accepted { .. }
        ));
        assert_eq!(
            tracker.attribute_pid(300, Some(145)),
            PidAttribution::Member {
                instance_id: child_id,
                comm: Some("process.exe".to_string()),
            }
        );
        assert_eq!(
            tracker.ingest_at(
                process_record(300, Some(1), Some(31)),
                EtwProcessPhase::Start,
                Some(150),
            ),
            IngestOutcome::Filtered
        );
        assert_ne!(
            tracker.attribute_pid(300, Some(155)),
            PidAttribution::Member {
                instance_id: child_id,
                comm: Some("process.exe".to_string()),
            }
        );

        // Ambiguous overlapping PID fails closed.
        assert!(matches!(
            tracker.ingest_at(
                process_record(400, Some(100), Some(40)),
                EtwProcessPhase::Start,
                Some(200),
            ),
            IngestOutcome::Accepted { .. }
        ));
        assert!(matches!(
            tracker.ingest_at(
                process_record(400, Some(100), Some(41)),
                EtwProcessPhase::Start,
                Some(210),
            ),
            IngestOutcome::Accepted { .. }
        ));
        assert_eq!(
            tracker.attribute_pid(400, Some(220)),
            PidAttribution::Ambiguous
        );
    }
}

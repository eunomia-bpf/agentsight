// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

pub use agentsight_capture_core::runners::{
    AgentRunner, BinaryRunner, EventStream, ProcessRunner, Runner, RunnerError,
};
pub use agentsight_capture_core::runners::common;
#[cfg(any(test, feature = "test-support"))]
pub use agentsight_capture_core::runners::FakeRunner;

mod system;
pub use system::{SystemConfig, SystemRunner};

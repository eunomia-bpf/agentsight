// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

use crate::output::{TopOptions, clear_screen, print_agent_top};
use crate::view::live_top::LiveView;
use crate::view::top::sort_agent_rows;
use std::io::{self, Write};
use std::time::Duration;

pub(crate) fn run_live_top_query(
    interval_secs: u64,
    limit: usize,
    count: Option<u32>,
    options: &TopOptions,
) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    let limit = limit.clamp(1, 100);
    let interval = Duration::from_secs(interval_secs.max(1));
    let mut iterations = 0u32;
    let should_clear_screen = count != Some(1);
    let mut live_view = LiveView::default();

    loop {
        if should_clear_screen {
            clear_screen();
        }
        let mut top = live_view.refresh(limit, options)?;
        sort_agent_rows(&mut top.rows, &options.sort);
        top.rows.truncate(limit);
        print_agent_top(&top);
        io::stdout().flush()?;

        iterations += 1;
        if count.is_some_and(|max| iterations >= max) || crate::shutdown_requested() {
            break;
        }
        std::thread::sleep(interval);
    }

    Ok(())
}

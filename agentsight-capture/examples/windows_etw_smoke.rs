#[cfg(windows)]
mod windows {
    use agentsight_capture_core::runners::WindowsEtwProcessRunner;
    use agentsight_capture_core::{Event, Runner};
    use futures::StreamExt;
    use std::process::{Child, Command, Stdio};
    use std::time::Duration;
    use tokio::time::{Instant, sleep, timeout};

    const START_DELAY: Duration = Duration::from_millis(1_500);
    const CHILD_LIFETIME: Duration = Duration::from_millis(1_000);
    const ROOT_EXIT_GRACE: Duration = Duration::from_millis(800);
    const CAPTURE_TIMEOUT: Duration = Duration::from_secs(10);

    type SmokeResult<T = ()> = Result<T, Box<dyn std::error::Error + Send + Sync>>;

    pub async fn run() -> SmokeResult {
        let current_exe = std::env::current_exe()?;
        let mut target = Command::new(&current_exe)
            .arg("--target-root")
            .stdout(Stdio::inherit())
            .stderr(Stdio::inherit())
            .spawn()?;
        let root_pid = target.id();
        println!("SMOKE target_root_pid={root_pid}");

        sleep(Duration::from_millis(300)).await;
        let result = capture(&root_pid).await;
        if result.is_err() {
            let _ = target.kill();
        }
        let status = target.wait()?;
        println!("SMOKE target_exit={status}");
        result
    }

    async fn capture(root_pid: &u32) -> SmokeResult {
        let mut stream = WindowsEtwProcessRunner::new(*root_pid).run().await?;
        let deadline = Instant::now() + CAPTURE_TIMEOUT;
        let mut root_present = false;
        let mut child_start = false;
        let mut child_exit = false;
        let mut root_exit = false;

        while Instant::now() < deadline {
            let event = timeout(deadline - Instant::now(), stream.next()).await;
            let Some(event) = event.ok().flatten() else {
                break;
            };
            println!("{}", serde_json::to_string(&event)?);
            match classify(&event, *root_pid) {
                Observation::RootPresent => root_present = true,
                Observation::RootExit => {
                    root_exit = true;
                    record_grace_events(&mut stream, *root_pid, &mut child_start, &mut child_exit)
                        .await?;
                    break;
                }
                Observation::ChildStart => child_start = true,
                Observation::ChildExit => child_exit = true,
                Observation::Other => {}
            }
        }

        drop(stream);
        if !(root_present && child_start && child_exit && root_exit) {
            return Err(format!(
                "missing lifecycle evidence: root_present={root_present} child_start={child_start} child_exit={child_exit} root_exit={root_exit}"
            )
            .into());
        }
        println!(
            "SMOKE PASS root_present={root_present} child_start={child_start} child_exit={child_exit} root_exit={root_exit}"
        );
        Ok(())
    }

    async fn record_grace_events(
        stream: &mut agentsight_capture_core::EventStream,
        root_pid: u32,
        child_start: &mut bool,
        child_exit: &mut bool,
    ) -> SmokeResult {
        let deadline = Instant::now() + ROOT_EXIT_GRACE;
        while Instant::now() < deadline {
            let Ok(Some(event)) = timeout(deadline - Instant::now(), stream.next()).await else {
                break;
            };
            println!("{}", serde_json::to_string(&event)?);
            match classify(&event, root_pid) {
                Observation::ChildStart => *child_start = true,
                Observation::ChildExit => *child_exit = true,
                Observation::RootPresent | Observation::RootExit | Observation::Other => {}
            }
        }
        Ok(())
    }

    fn classify(event: &Event, root_pid: u32) -> Observation {
        if event.source != "process" {
            return Observation::Other;
        }
        match (event.pid == root_pid, event.data["event"].as_str()) {
            (true, Some("EXEC" | "PROCESS_PRESENT")) => Observation::RootPresent,
            (true, Some("EXIT")) => Observation::RootExit,
            (false, Some("EXEC")) => Observation::ChildStart,
            (false, Some("EXIT")) => Observation::ChildExit,
            _ => Observation::Other,
        }
    }

    enum Observation {
        RootPresent,
        RootExit,
        ChildStart,
        ChildExit,
        Other,
    }

    pub async fn target_root() -> SmokeResult {
        let current_exe = std::env::current_exe()?;
        sleep(START_DELAY).await;
        let mut child: Child = Command::new(current_exe)
            .arg("--target-child")
            .stdout(Stdio::inherit())
            .stderr(Stdio::inherit())
            .spawn()?;
        println!("SMOKE target_child_pid={}", child.id());
        let status = child.wait()?;
        println!("SMOKE target_child_exit={status}");
        sleep(ROOT_EXIT_GRACE).await;
        Ok(())
    }

    pub async fn target_child() -> SmokeResult {
        println!("SMOKE target_child_pid={}", std::process::id());
        sleep(CHILD_LIFETIME).await;
        Ok(())
    }
}

#[cfg(windows)]
#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    match std::env::args().nth(1).as_deref() {
        Some("--target-root") => windows::target_root().await,
        Some("--target-child") => windows::target_child().await,
        None => windows::run().await,
        Some(other) => Err(format!("unknown smoke argument: {other}").into()),
    }
}

#[cfg(not(windows))]
fn main() {
    eprintln!("windows_etw_smoke is Windows-only");
    std::process::exit(2);
}

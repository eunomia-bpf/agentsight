#[cfg(windows)]
mod windows {
    use agentsight_capture_core::runners::WindowsEtwProcessRunner;
    use agentsight_capture_core::{Event, Runner};
    use futures::StreamExt;
    use std::net::{TcpListener, TcpStream, UdpSocket};
    use std::process::{Child, Command, Stdio};
    use std::time::Duration;
    use tokio::time::{Instant, sleep, timeout};

    const START_DELAY: Duration = Duration::from_millis(1_500);
    const CHILD_LIFETIME: Duration = Duration::from_millis(1_000);
    const ROOT_EXIT_GRACE: Duration = Duration::from_millis(800);
    const CAPTURE_TIMEOUT: Duration = Duration::from_secs(10);

    type SmokeResult<T = ()> = Result<T, Box<dyn std::error::Error + Send + Sync>>;

    pub async fn run(with_network: bool) -> SmokeResult {
        let current_exe = std::env::current_exe()?;
        let mut cmd = Command::new(&current_exe);
        cmd.arg("--target-root");
        if with_network {
            cmd.arg("--with-network");
        }
        let mut target = cmd
            .stdout(Stdio::inherit())
            .stderr(Stdio::inherit())
            .spawn()?;
        let root_pid = target.id();
        println!("SMOKE target_root_pid={root_pid} with_network={with_network}");

        sleep(Duration::from_millis(300)).await;
        let result = capture(&root_pid, with_network).await;
        if result.is_err() {
            let _ = target.kill();
        }
        let status = target.wait()?;
        println!("SMOKE target_exit={status}");
        result
    }

    async fn capture(root_pid: &u32, with_network: bool) -> SmokeResult {
        let mut stream = WindowsEtwProcessRunner::new(*root_pid)
            .with_network(with_network)
            .run()
            .await?;
        let deadline = Instant::now() + CAPTURE_TIMEOUT;
        let mut obs = SmokeObservations::default();

        while Instant::now() < deadline {
            let event = timeout(deadline - Instant::now(), stream.next()).await;
            let Some(event) = event.ok().flatten() else {
                break;
            };
            println!("{}", serde_json::to_string(&event)?);
            observe(&event, *root_pid, &mut obs);
            if obs.root_exit {
                record_grace_events(&mut stream, *root_pid, &mut obs).await?;
                break;
            }
        }

        drop(stream);
        if !(obs.root_present && obs.child_start && obs.child_exit && obs.root_exit) {
            return Err(format!(
                "missing lifecycle evidence: root_present={} child_start={} child_exit={} root_exit={}",
                obs.root_present, obs.child_start, obs.child_exit, obs.root_exit
            )
            .into());
        }
        if with_network && !obs.net_connect {
            return Err(format!(
                "missing network evidence: net_connect={} net_accept={} net_disconnect={} net_udp_send={}",
                obs.net_connect, obs.net_accept, obs.net_disconnect, obs.net_udp_send
            )
            .into());
        }
        println!(
            "SMOKE PASS root_present={} child_start={} child_exit={} root_exit={} net_connect={} net_accept={} net_disconnect={} net_udp_send={}",
            obs.root_present,
            obs.child_start,
            obs.child_exit,
            obs.root_exit,
            obs.net_connect,
            obs.net_accept,
            obs.net_disconnect,
            obs.net_udp_send
        );
        Ok(())
    }

    async fn record_grace_events(
        stream: &mut agentsight_capture_core::EventStream,
        root_pid: u32,
        obs: &mut SmokeObservations,
    ) -> SmokeResult {
        let deadline = Instant::now() + ROOT_EXIT_GRACE;
        while Instant::now() < deadline {
            let Ok(Some(event)) = timeout(deadline - Instant::now(), stream.next()).await else {
                break;
            };
            println!("{}", serde_json::to_string(&event)?);
            observe(&event, root_pid, obs);
        }
        Ok(())
    }

    #[derive(Default)]
    struct SmokeObservations {
        root_present: bool,
        child_start: bool,
        child_exit: bool,
        root_exit: bool,
        net_connect: bool,
        net_accept: bool,
        net_disconnect: bool,
        net_udp_send: bool,
    }

    fn observe(event: &Event, root_pid: u32, obs: &mut SmokeObservations) {
        if event.source != "process" {
            return;
        }
        match (event.pid == root_pid, event.data["event"].as_str()) {
            (true, Some("EXEC" | "PROCESS_PRESENT")) => obs.root_present = true,
            (true, Some("EXIT")) => obs.root_exit = true,
            (false, Some("EXEC")) => obs.child_start = true,
            (false, Some("EXIT")) => obs.child_exit = true,
            (_, Some("NET_CONNECT")) => obs.net_connect = true,
            (_, Some("NET_ACCEPT")) => obs.net_accept = true,
            (_, Some("NET_DISCONNECT")) => obs.net_disconnect = true,
            (_, Some("NET_UDP_SEND")) => obs.net_udp_send = true,
            _ => {}
        }
    }

    pub async fn target_root(with_network: bool) -> SmokeResult {
        let current_exe = std::env::current_exe()?;
        sleep(START_DELAY).await;
        let mut cmd = Command::new(current_exe);
        cmd.arg("--target-child");
        if with_network {
            cmd.arg("--with-network");
        }
        let mut child: Child = cmd
            .stdout(Stdio::inherit())
            .stderr(Stdio::inherit())
            .spawn()?;
        println!("SMOKE target_child_pid={}", child.id());
        let status = child.wait()?;
        println!("SMOKE target_child_exit={status}");
        sleep(ROOT_EXIT_GRACE).await;
        Ok(())
    }

    pub async fn target_child(with_network: bool) -> SmokeResult {
        println!(
            "SMOKE target_child_pid={} with_network={with_network}",
            std::process::id()
        );
        if with_network {
            let listener = TcpListener::bind("127.0.0.1:0")?;
            let listener_addr = listener.local_addr()?;
            println!("SMOKE target_tcp_listener={listener_addr}");
            let accept_thread = std::thread::spawn(move || {
                let _ = listener.accept();
            });
            let stream = TcpStream::connect(listener_addr)?;
            println!("SMOKE target_tcp_client={}", stream.local_addr()?);
            drop(stream);
            let _ = accept_thread.join();

            let udp_sink = UdpSocket::bind("127.0.0.1:0")?;
            let udp_sender = UdpSocket::bind("127.0.0.1:0")?;
            let udp_target = udp_sink.local_addr()?;
            let _ = udp_sender.send_to(b"agentsight-etw-udp-smoke", udp_target)?;
            println!("SMOKE target_udp_sent={udp_target}");
        }
        sleep(CHILD_LIFETIME).await;
        Ok(())
    }
}

#[cfg(windows)]
#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    let args: Vec<String> = std::env::args().skip(1).collect();
    let mut with_network = false;
    let mut mode: Option<&str> = None;
    for arg in &args {
        match arg.as_str() {
            "--with-network" => with_network = true,
            "--target-root" | "--target-child" if mode.is_none() => mode = Some(arg.as_str()),
            other => return Err(format!("unknown smoke argument: {other}").into()),
        }
    }
    match mode {
        Some("--target-root") => windows::target_root(with_network).await,
        Some("--target-child") => windows::target_child(with_network).await,
        None => windows::run(with_network).await,
        Some(other) => Err(format!("unknown smoke argument: {other}").into()),
    }
}

#[cfg(not(windows))]
fn main() {
    eprintln!("windows_etw_smoke is Windows-only");
    std::process::exit(2);
}

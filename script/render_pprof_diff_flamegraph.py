#!/usr/bin/env python3
"""Capture stock pprof's combined differential flamegraph for paper use.

The script does not implement a flamegraph renderer. It starts ``go tool
pprof``, opens pprof's own flamegraph page in headless Chrome, isolates the
rendered chart, and exports that chart as a vector PDF or high-resolution PNG.
"""

from __future__ import annotations

import argparse
import base64
import json
import shutil
import socket
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

try:
    import websocket
except ImportError as error:  # pragma: no cover - environment dependency
    raise SystemExit(
        "render_pprof_diff_flamegraph.py requires the websocket-client package"
    ) from error


DEFAULT_BROWSER_CANDIDATES = ("chromium", "chromium-browser", "google-chrome")


class CdpClient:
    def __init__(self, url: str) -> None:
        self._socket = websocket.create_connection(
            url,
            timeout=10,
            http_proxy_host=None,
            http_proxy_port=None,
        )
        self._next_id = 0

    def close(self) -> None:
        self._socket.close()

    def call(self, method: str, params: dict[str, Any] | None = None) -> Any:
        self._next_id += 1
        request_id = self._next_id
        self._socket.send(
            json.dumps(
                {
                    "id": request_id,
                    "method": method,
                    "params": params or {},
                }
            )
        )
        while True:
            response = json.loads(self._socket.recv())
            if response.get("id") != request_id:
                continue
            if "error" in response:
                raise RuntimeError(f"Chrome DevTools error for {method}: {response['error']}")
            return response.get("result", {})


def reserve_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def wait_json(url: str, timeout: float = 15.0) -> Any:
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                return json.load(response)
        except (OSError, urllib.error.URLError, json.JSONDecodeError) as error:
            last_error = error
            time.sleep(0.1)
    raise RuntimeError(f"timed out waiting for {url}: {last_error}")


def wait_http(url: str, timeout: float = 15.0) -> None:
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                if response.status == 200:
                    return
        except (OSError, urllib.error.URLError) as error:
            last_error = error
            time.sleep(0.1)
    raise RuntimeError(f"timed out waiting for {url}: {last_error}")


def wait_page_target(
    debug_port: int, expected_url: str, timeout: float = 15.0
) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    fallback: dict[str, Any] | None = None
    while time.monotonic() < deadline:
        targets = wait_json(f"http://127.0.0.1:{debug_port}/json/list", timeout=1)
        for target in targets:
            if target.get("type") != "page":
                continue
            fallback = target
            if str(target.get("url", "")).startswith(expected_url):
                return target
        time.sleep(0.1)
    if fallback is not None:
        return fallback
    raise RuntimeError("headless Chrome exposed no page target")


def find_browser(explicit: str | None) -> str:
    if explicit:
        resolved = shutil.which(explicit)
        if resolved:
            return resolved
        path = Path(explicit)
        if path.is_file():
            return str(path)
        raise RuntimeError(f"browser does not exist: {explicit}")
    for candidate in DEFAULT_BROWSER_CANDIDATES:
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    raise RuntimeError(
        "Google Chrome or Chromium is required to capture stock pprof output"
    )


def terminate(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def wait_for_chart(client: CdpClient, timeout: float = 15.0) -> dict[str, float]:
    expression = """
(() => {
  const chart = document.querySelector('#stack-chart');
  if (!chart || chart.children.length === 0) return null;
  const rect = chart.getBoundingClientRect();
  if (rect.width <= 0 || rect.height <= 0) return null;
  return {width: Math.ceil(rect.width), height: Math.ceil(rect.height)};
})()
"""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        result = client.call(
            "Runtime.evaluate",
            {"expression": expression, "returnByValue": True},
        )
        value = result.get("result", {}).get("value")
        if value:
            return {"width": float(value["width"]), "height": float(value["height"])}
        time.sleep(0.1)
    raise RuntimeError("stock pprof flamegraph did not render")


def isolate_chart(client: CdpClient) -> dict[str, float]:
    expression = """
(() => {
  const chart = document.querySelector('#stack-chart');
  if (!chart) throw new Error('missing #stack-chart');
  const rect = chart.getBoundingClientRect();
  const width = Math.ceil(rect.width);
  const height = Math.ceil(rect.height);
  chart.remove();
  chart.style.position = 'relative';
  chart.style.width = `${width}px`;
  chart.style.height = `${height}px`;
  document.body.replaceChildren(chart);
  document.body.style.margin = '0';
  document.body.style.padding = '0';
  document.body.style.background = 'white';
  document.documentElement.style.background = 'white';
  return {width, height};
})()
"""
    result = client.call(
        "Runtime.evaluate",
        {"expression": expression, "returnByValue": True},
    )
    if "exceptionDetails" in result:
        raise RuntimeError(f"could not isolate pprof chart: {result['exceptionDetails']}")
    value = result.get("result", {}).get("value")
    if not value:
        raise RuntimeError("could not determine isolated pprof chart dimensions")
    return {"width": float(value["width"]), "height": float(value["height"])}


def render(args: argparse.Namespace) -> dict[str, Any]:
    profile = args.profile.resolve()
    output = args.output.resolve()
    if not profile.is_file():
        raise RuntimeError(f"profile does not exist: {profile}")
    if not (profile.name.endswith(".pb") or profile.name.endswith(".pb.gz")):
        raise RuntimeError("profile must be a standard .pb or .pb.gz pprof")
    if output.suffix.lower() not in {".pdf", ".png"}:
        raise RuntimeError("output must end in .pdf or .png")
    output.parent.mkdir(parents=True, exist_ok=True)

    browser = find_browser(args.browser)
    pprof_port = reserve_port()
    chrome_port = reserve_port()
    pprof_url = f"http://127.0.0.1:{pprof_port}/ui/flamegraph"
    pprof_command = [
        "go",
        "tool",
        "pprof",
        f"-http=127.0.0.1:{pprof_port}",
        "-no_browser",
    ]
    if args.focus:
        pprof_command.append(f"-focus={args.focus}")
    if args.hide:
        pprof_command.append(f"-hide={args.hide}")
    pprof_command.append(str(profile))

    pprof_process = subprocess.Popen(
        pprof_command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    chrome_process: subprocess.Popen[bytes] | None = None
    client: CdpClient | None = None
    try:
        wait_http(pprof_url)
        with tempfile.TemporaryDirectory(prefix="agentpprof-chrome-") as chrome_data:
            chrome_process = subprocess.Popen(
                [
                    browser,
                    "--headless",
                    "--no-sandbox",
                    "--disable-gpu",
                    "--hide-scrollbars",
                    "--remote-allow-origins=*",
                    f"--remote-debugging-port={chrome_port}",
                    f"--user-data-dir={chrome_data}",
                    f"--window-size={args.width},{args.height}",
                    f"--force-device-scale-factor={args.device_scale}",
                    pprof_url,
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            page = wait_page_target(chrome_port, pprof_url)
            client = CdpClient(str(page["webSocketDebuggerUrl"]))
            client.call("Page.enable")
            client.call("Runtime.enable")
            client.call(
                "Emulation.setDeviceMetricsOverride",
                {
                    "width": args.width,
                    "height": args.height,
                    "deviceScaleFactor": args.device_scale,
                    "mobile": False,
                },
            )
            wait_for_chart(client)
            chart = isolate_chart(client)

            if output.suffix.lower() == ".pdf":
                result = client.call(
                    "Page.printToPDF",
                    {
                        "printBackground": True,
                        "displayHeaderFooter": False,
                        "preferCSSPageSize": False,
                        "paperWidth": chart["width"] / 96.0,
                        "paperHeight": chart["height"] / 96.0,
                        "marginTop": 0,
                        "marginBottom": 0,
                        "marginLeft": 0,
                        "marginRight": 0,
                        "pageRanges": "1",
                    },
                )
            else:
                result = client.call(
                    "Page.captureScreenshot",
                    {
                        "format": "png",
                        "fromSurface": True,
                        "captureBeyondViewport": True,
                        "clip": {
                            "x": 0,
                            "y": 0,
                            "width": chart["width"],
                            "height": chart["height"],
                            "scale": 1,
                        },
                    },
                )
            output.write_bytes(base64.b64decode(result["data"]))
            return {
                "status": "ok",
                "profile": str(profile),
                "output": str(output),
                "renderer": "stock-go-pprof",
                "focus": args.focus,
                "hide": args.hide,
                "chart_css_width": int(chart["width"]),
                "chart_css_height": int(chart["height"]),
                "device_scale": args.device_scale,
            }
    finally:
        if client is not None:
            client.close()
        if chrome_process is not None:
            terminate(chrome_process)
        terminate(pprof_process)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--focus", help="pprof-compatible frame regular expression")
    parser.add_argument("--hide", help="pprof-compatible frame regular expression")
    parser.add_argument("--browser", help="Chrome/Chromium executable")
    parser.add_argument("--width", type=int, default=1100, help="CSS viewport width")
    parser.add_argument("--height", type=int, default=400, help="CSS viewport height")
    parser.add_argument(
        "--device-scale",
        type=float,
        default=2.0,
        help="device scale for high-resolution PNG output",
    )
    args = parser.parse_args()
    try:
        result = render(args)
    except RuntimeError as error:
        parser.error(str(error))
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

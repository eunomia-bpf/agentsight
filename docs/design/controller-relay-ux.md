# AgentSight Controller, Relay, and Fleet UX

Status: implementation plan for the first usable hosted fleet experience.

## Product contract

The hosted app is a fleet client, not a telemetry warehouse.

- The AgentSight Node owns session, process, prompt, tool, and system evidence.
- The AgentSight Controller owns user identity, Node ownership, discovery metadata, and online routing.
- The browser tries a known Direct path first and falls back to Controller Relay.
- Relay forwards an allowlisted Node Protocol request and does not persist the response body.
- A signed-in browser never receives the Node's Direct bearer from the Controller.
- One persistent Node bearer is reused for local Direct authorization and Node-to-Controller relay authentication in this first slice. The Controller stores only its SHA-256 hash.

```text
                         identity / registry
                   +--------------------------+
                   |                          v
Browser ---------->| AgentSight Controller ---+--- D1 metadata
   |               |          |
   |               |          v
   |               |     Node Relay (DO)
   |               |          ^
   |               +----------|--- outbound WSS
   |                          |
   +-------- Direct HTTP ---->+ AgentSight Node ----> local evidence / SQLite
```

Direct remains the preferred path for localhost, LAN, VPN, Tailscale, or a public Node endpoint. Relay exists so a fresh browser can open an online Node behind NAT without first copying an endpoint or secret into that browser.

## Main user journey

### Signed-in user

The app opens directly into a fleet shell.

1. Left sidebar lists the user's Machines.
2. Clicking a Machine immediately tries a saved Direct connection for that Node.
3. If Direct is absent or unreachable, the app asks the Controller for the Node through Relay.
4. A successful Node opens its Sessions workspace.
5. Selecting a Session shows the native conversation, tools, and current progress.
6. The composer submits to the selected native session through the same active transport.
7. Overview, timeline, process tree, event log, and metrics remain secondary inspection tabs.

There is no metadata-only Node card that looks clickable but is not actionable.

### Fresh browser

A fresh browser has only the signed-in Controller session. It can still click any relay-enabled, online Node in the account. The Controller verifies Node ownership, then forwards the request to the Node's outbound WSS connection. Direct bearer material is never returned to the browser.

### Local anonymous user

A user can still run `agentsight bind` and use the Direct Node without creating an account. Signing in adds ownership/discovery/relay; it is not required for local data collection or local querying.

## App information architecture

The fleet shell uses one persistent navigation hierarchy:

```text
Machines
  workstation
  gpu-box
  server

Selected machine
  Sessions     <- default
  Overview
  Timeline
  Processes
  Events
  Metrics
```

The selected Node header shows the actual data path (`Direct`, `Relay`, or `Embedded`) and an explicit offline/error state. `Registered` is not presented as equivalent to online.

The Sessions workspace is the operational home:

- session list on the left;
- conversation/progress in the main pane;
- tool/effect events inline but visually quieter than messages;
- composer pinned at the bottom when the session is writable;
- selected session detail refreshes while visible;
- after submit, the UI shows that the message was accepted and keeps refreshing until newer agent output appears.

## Relay protocol

The Controller exposes only these browser operations in this slice:

- Node relay status;
- snapshot read;
- native session detail read;
- native session message submit.

The Controller does not accept arbitrary target URLs or arbitrary Node paths.

Node-to-Controller WSS messages use a small request/response envelope:

```json
{"type":"request","id":"...","method":"GET","path":"/api/v1/snapshot?audit_limit=5000"}
{"type":"response","id":"...","status":200,"body":"{...}"}
```

The Node validates the method/path again before issuing the request to its own local API. This avoids turning Relay into SSRF or a general remote shell transport.

## Enrollment and authentication

`agentsight bind` already creates a persistent Node ID and persistent Direct bearer. When a signed-in browser successfully binds the Node, Node registration additionally sends that bearer to the Controller over HTTPS. The Controller hashes it immediately and stores only the hash.

The Node opens an outbound authenticated WSS connection using the same bearer. Until the browser has enrolled the Node into an account, the Controller rejects that connection and the Node retries quietly.

Browser relay requests use the user's normal Controller bearer. The Controller authorizes `user -> node` ownership before routing to that Node's relay object.

This deliberately avoids a second capability/auth API in the P0 slice. Public-key Node identity and short-lived delegated capabilities can replace the shared bearer later without changing the frontend transport abstraction.

## Non-goals for this slice

- No raw telemetry warehouse in Controller/D1.
- No arbitrary SQL or arbitrary HTTP relay.
- No WebRTC/ICE/NAT traversal implementation.
- No multi-region Site Gateway.
- No E2E-blind relay claim: P0 response data transits Controller runtime memory even though it is not persisted.
- No takeover of externally owned agent TUIs; native-session control keeps the #159 runtime rules.

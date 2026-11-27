// SPDX-License-Identifier: MIT
// Copyright (c) 2026 eunomia-bpf org.

//! Schema-driven decoder for classic Windows ETW `TcpIp` and `UdpIp` kernel events.

use std::net::{IpAddr, Ipv4Addr, Ipv6Addr, SocketAddr};

/// Classic ETW `TcpIp` kernel provider GUID (`{9a280ac0-c8e0-11d1-84e2-00c04fb998a2}`).
pub(super) const TCPIP_PROVIDER_GUID: windows_sys::core::GUID =
    windows_sys::core::GUID::from_u128(0x9a280ac0_c8e0_11d1_84e2_00c04fb998a2);

/// Classic ETW `UdpIp` kernel provider GUID (`{bf3a50c5-a9c9-4988-a005-2df0b7c80f80}`).
pub(super) const UDPIP_PROVIDER_GUID: windows_sys::core::GUID =
    windows_sys::core::GUID::from_u128(0xbf3a50c5_a9c9_4988_a005_2df0b7c80f80);

pub(super) const TCPIP_PROVIDER_GUID_STR: &str = "9a280ac0-c8e0-11d1-84e2-00c04fb998a2";
pub(super) const UDPIP_PROVIDER_GUID_STR: &str = "bf3a50c5-a9c9-4988-a005-2df0b7c80f80";

pub(super) mod tcpip_opcode {
    pub(crate) const SEND_IPV4: u8 = 10;
    pub(crate) const RECV_IPV4: u8 = 11;
    pub(crate) const CONNECT_IPV4: u8 = 12;
    pub(crate) const DISCONNECT_IPV4: u8 = 13;
    pub(crate) const RETRANSMIT_IPV4: u8 = 14;
    pub(crate) const ACCEPT_IPV4: u8 = 15;
    pub(crate) const RECONNECT_IPV4: u8 = 16;
    #[cfg(test)]
    pub(crate) const FAIL: u8 = 17;
    pub(crate) const TCP_COPY_IPV4: u8 = 18;
    pub(crate) const SEND_IPV6: u8 = 26;
    pub(crate) const RECV_IPV6: u8 = 27;
    pub(crate) const CONNECT_IPV6: u8 = 28;
    pub(crate) const DISCONNECT_IPV6: u8 = 29;
    pub(crate) const RETRANSMIT_IPV6: u8 = 30;
    pub(crate) const ACCEPT_IPV6: u8 = 31;
    pub(crate) const RECONNECT_IPV6: u8 = 32;
    pub(crate) const TCP_COPY_IPV6: u8 = 34;
}

pub(super) mod udpip_opcode {
    pub(crate) const SEND_IPV4: u8 = 10;
    pub(crate) const RECV_IPV4: u8 = 11;
    #[cfg(test)]
    pub(crate) const FAIL: u8 = 17;
    pub(crate) const SEND_IPV6: u8 = 26;
    pub(crate) const RECV_IPV6: u8 = 27;
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(super) enum EtwNetworkProvider {
    TcpIp,
    UdpIp,
}

impl EtwNetworkProvider {
    pub(super) fn as_str(self) -> &'static str {
        match self {
            Self::TcpIp => "TcpIp",
            Self::UdpIp => "UdpIp",
        }
    }

    pub(super) fn guid_str(self) -> &'static str {
        match self {
            Self::TcpIp => TCPIP_PROVIDER_GUID_STR,
            Self::UdpIp => UDPIP_PROVIDER_GUID_STR,
        }
    }

    pub(super) fn protocol(self) -> &'static str {
        match self {
            Self::TcpIp => "tcp",
            Self::UdpIp => "udp",
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(super) enum EtwNetworkOp {
    TcpConnect,
    TcpAccept,
    TcpDisconnect,
    TcpReconnect,
    TcpSend,
    TcpRecv,
    TcpRetransmit,
    TcpCopy,
    UdpSend,
    UdpRecv,
}

impl EtwNetworkOp {
    pub(super) fn event_name(self) -> &'static str {
        match self {
            Self::TcpConnect => "NET_CONNECT",
            Self::TcpAccept => "NET_ACCEPT",
            Self::TcpDisconnect => "NET_DISCONNECT",
            Self::TcpReconnect => "NET_RECONNECT",
            Self::TcpSend => "NET_TCP_SEND",
            Self::TcpRecv => "NET_TCP_RECV",
            Self::TcpRetransmit => "NET_TCP_RETRANSMIT",
            Self::TcpCopy => "NET_TCP_COPY",
            Self::UdpSend => "NET_UDP_SEND",
            Self::UdpRecv => "NET_UDP_RECV",
        }
    }

    pub(super) fn operation_name(self, ip_version: u8) -> &'static str {
        match (self, ip_version) {
            (Self::TcpConnect, 6) => "ConnectIPV6",
            (Self::TcpConnect, _) => "ConnectIPV4",
            (Self::TcpAccept, 6) => "AcceptIPV6",
            (Self::TcpAccept, _) => "AcceptIPV4",
            (Self::TcpDisconnect, 6) => "DisconnectIPV6",
            (Self::TcpDisconnect, _) => "DisconnectIPV4",
            (Self::TcpReconnect, 6) => "ReconnectIPV6",
            (Self::TcpReconnect, _) => "ReconnectIPV4",
            (Self::TcpSend, 6) => "SendIPV6",
            (Self::TcpSend, _) => "SendIPV4",
            (Self::TcpRecv, 6) => "RecvIPV6",
            (Self::TcpRecv, _) => "RecvIPV4",
            (Self::TcpRetransmit, 6) => "RetransmitIPV6",
            (Self::TcpRetransmit, _) => "RetransmitIPV4",
            (Self::TcpCopy, 6) => "TCPCopyIPV6",
            (Self::TcpCopy, _) => "TCPCopyIPV4",
            (Self::UdpSend, 6) => "SendIPV6",
            (Self::UdpSend, _) => "SendIPV4",
            (Self::UdpRecv, 6) => "RecvIPV6",
            (Self::UdpRecv, _) => "RecvIPV4",
        }
    }
}

/// Callback-stage opcode allowlist that drops high-volume per-packet `Send`/`Recv`
/// TCP traffic, inbound UDP noise, and PID-less `Fail` events before allocation.
pub(super) fn should_capture_in_callback(provider: EtwNetworkProvider, opcode: u8) -> bool {
    match provider {
        EtwNetworkProvider::TcpIp => matches!(
            opcode,
            tcpip_opcode::CONNECT_IPV4
                | tcpip_opcode::DISCONNECT_IPV4
                | tcpip_opcode::ACCEPT_IPV4
                | tcpip_opcode::RECONNECT_IPV4
                | tcpip_opcode::CONNECT_IPV6
                | tcpip_opcode::DISCONNECT_IPV6
                | tcpip_opcode::ACCEPT_IPV6
                | tcpip_opcode::RECONNECT_IPV6
        ),
        EtwNetworkProvider::UdpIp => {
            matches!(opcode, udpip_opcode::SEND_IPV4 | udpip_opcode::SEND_IPV6)
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub(super) struct NetworkEtwRecord {
    pub(super) provider: EtwNetworkProvider,
    pub(super) operation: EtwNetworkOp,
    pub(super) ip_version: u8,
    pub(super) pid: u32,
    pub(super) size: u32,
    pub(super) daddr: IpAddr,
    pub(super) saddr: IpAddr,
    pub(super) dport: u16,
    pub(super) sport: u16,
    pub(super) seqnum: Option<u32>,
    pub(super) conn_id: Option<u32>,
}

impl NetworkEtwRecord {
    pub(super) fn local_endpoint(&self) -> String {
        SocketAddr::new(self.saddr, self.sport).to_string()
    }

    pub(super) fn peer_endpoint(&self) -> String {
        SocketAddr::new(self.daddr, self.dport).to_string()
    }

    pub(super) fn primary_port(&self) -> u16 {
        match self.operation {
            EtwNetworkOp::TcpAccept => self.sport,
            _ => self.dport,
        }
    }
}

struct NetCursor<'a> {
    data: &'a [u8],
    pos: usize,
}

impl<'a> NetCursor<'a> {
    fn new(data: &'a [u8]) -> Self {
        Self { data, pos: 0 }
    }

    fn skip(&mut self, len: usize) -> bool {
        if self.data.len().saturating_sub(self.pos) < len {
            return false;
        }
        self.pos += len;
        true
    }

    fn u32_le(&mut self) -> Option<u32> {
        let end = self.pos.checked_add(4)?;
        let bytes = self.data.get(self.pos..end)?;
        self.pos = end;
        Some(u32::from_le_bytes(bytes.try_into().ok()?))
    }

    fn u16_be(&mut self) -> Option<u16> {
        let end = self.pos.checked_add(2)?;
        let bytes = self.data.get(self.pos..end)?;
        self.pos = end;
        Some(u16::from_be_bytes(bytes.try_into().ok()?))
    }

    fn ipv4(&mut self) -> Option<IpAddr> {
        let end = self.pos.checked_add(4)?;
        let bytes = self.data.get(self.pos..end)?;
        self.pos = end;
        let octets: [u8; 4] = bytes.try_into().ok()?;
        Some(IpAddr::V4(Ipv4Addr::from(octets)))
    }

    fn ipv6(&mut self) -> Option<IpAddr> {
        let end = self.pos.checked_add(16)?;
        let bytes = self.data.get(self.pos..end)?;
        self.pos = end;
        let octets: [u8; 16] = bytes.try_into().ok()?;
        Some(IpAddr::V6(Ipv6Addr::from(octets)))
    }

    fn ip_addr(&mut self, ip_version: u8) -> Option<IpAddr> {
        match ip_version {
            4 => self.ipv4(),
            6 => self.ipv6(),
            _ => None,
        }
    }
}

/// Decodes a classic ETW `TcpIp` or `UdpIp` payload according to its provider,
/// opcode, and MOF schema version.
pub(super) fn parse_network_event(
    provider: EtwNetworkProvider,
    opcode: u8,
    version: u8,
    data: &[u8],
) -> Option<NetworkEtwRecord> {
    match provider {
        EtwNetworkProvider::TcpIp => parse_tcpip_event(opcode, version, data),
        EtwNetworkProvider::UdpIp => parse_udpip_event(opcode, version, data),
    }
}

#[derive(Clone, Copy)]
enum TcpLayout {
    Standard,
    ConnectAccept,
    Send,
}

fn classify_tcpip_opcode(opcode: u8) -> Option<(EtwNetworkOp, u8, TcpLayout)> {
    match opcode {
        tcpip_opcode::SEND_IPV4 => Some((EtwNetworkOp::TcpSend, 4, TcpLayout::Send)),
        tcpip_opcode::RECV_IPV4 => Some((EtwNetworkOp::TcpRecv, 4, TcpLayout::Standard)),
        tcpip_opcode::CONNECT_IPV4 => {
            Some((EtwNetworkOp::TcpConnect, 4, TcpLayout::ConnectAccept))
        }
        tcpip_opcode::DISCONNECT_IPV4 => {
            Some((EtwNetworkOp::TcpDisconnect, 4, TcpLayout::Standard))
        }
        tcpip_opcode::RETRANSMIT_IPV4 => {
            Some((EtwNetworkOp::TcpRetransmit, 4, TcpLayout::Standard))
        }
        tcpip_opcode::ACCEPT_IPV4 => Some((EtwNetworkOp::TcpAccept, 4, TcpLayout::ConnectAccept)),
        tcpip_opcode::RECONNECT_IPV4 => Some((EtwNetworkOp::TcpReconnect, 4, TcpLayout::Standard)),
        tcpip_opcode::TCP_COPY_IPV4 => Some((EtwNetworkOp::TcpCopy, 4, TcpLayout::Standard)),
        tcpip_opcode::SEND_IPV6 => Some((EtwNetworkOp::TcpSend, 6, TcpLayout::Send)),
        tcpip_opcode::RECV_IPV6 => Some((EtwNetworkOp::TcpRecv, 6, TcpLayout::Standard)),
        tcpip_opcode::CONNECT_IPV6 => {
            Some((EtwNetworkOp::TcpConnect, 6, TcpLayout::ConnectAccept))
        }
        tcpip_opcode::DISCONNECT_IPV6 => {
            Some((EtwNetworkOp::TcpDisconnect, 6, TcpLayout::Standard))
        }
        tcpip_opcode::RETRANSMIT_IPV6 => {
            Some((EtwNetworkOp::TcpRetransmit, 6, TcpLayout::Standard))
        }
        tcpip_opcode::ACCEPT_IPV6 => Some((EtwNetworkOp::TcpAccept, 6, TcpLayout::ConnectAccept)),
        tcpip_opcode::RECONNECT_IPV6 => Some((EtwNetworkOp::TcpReconnect, 6, TcpLayout::Standard)),
        tcpip_opcode::TCP_COPY_IPV6 => Some((EtwNetworkOp::TcpCopy, 6, TcpLayout::Standard)),
        _ => None,
    }
}

fn parse_tcpip_event(opcode: u8, version: u8, data: &[u8]) -> Option<NetworkEtwRecord> {
    let (operation, ip_version, layout) = classify_tcpip_opcode(opcode)?;
    let mut cursor = NetCursor::new(data);

    match version {
        0 => {
            // TcpIp_V0_TypeGroup1 only defines IPv4 opcodes 10..=15.
            if ip_version != 4 || !matches!(opcode, 10..=15) {
                return None;
            }
            let daddr = cursor.ip_addr(4)?;
            let saddr = cursor.ip_addr(4)?;
            let dport = cursor.u16_be()?;
            let sport = cursor.u16_be()?;
            let size = cursor.u32_le()?;
            let pid = cursor.u32_le()?;
            Some(NetworkEtwRecord {
                provider: EtwNetworkProvider::TcpIp,
                operation,
                ip_version: 4,
                pid,
                size,
                daddr,
                saddr,
                dport,
                sport,
                seqnum: None,
                conn_id: None,
            })
        }
        1 | 2 => {
            // TcpIp v1 only defines IPv4 MOF classes; reject IPv6 opcodes under v1.
            if version == 1 && ip_version != 4 {
                return None;
            }
            let pid = cursor.u32_le()?;
            let size = cursor.u32_le()?;
            let daddr = cursor.ip_addr(ip_version)?;
            let saddr = cursor.ip_addr(ip_version)?;
            let dport = cursor.u16_be()?;
            let sport = cursor.u16_be()?;

            match layout {
                // mss(2), sackopt(2), tsopt(2), wsopt(2), rcvwin(4), rcvwinscale(2), sndwinscale(2)
                TcpLayout::ConnectAccept => {
                    if !cursor.skip(16) {
                        return None;
                    }
                }
                // startime(4), endtime(4)
                TcpLayout::Send => {
                    if !cursor.skip(8) {
                        return None;
                    }
                }
                TcpLayout::Standard => {}
            }

            // TcpIp v1 orders `connid` before `seqnum`; v2 orders `seqnum` before `connid`.
            let (seqnum, conn_id) = if version == 1 {
                let conn_id = cursor.u32_le()?;
                let seqnum = cursor.u32_le()?;
                (seqnum, conn_id)
            } else {
                let seqnum = cursor.u32_le()?;
                let conn_id = cursor.u32_le()?;
                (seqnum, conn_id)
            };

            Some(NetworkEtwRecord {
                provider: EtwNetworkProvider::TcpIp,
                operation,
                ip_version,
                pid,
                size,
                daddr,
                saddr,
                dport,
                sport,
                seqnum: Some(seqnum),
                conn_id: Some(conn_id),
            })
        }
        _ => None,
    }
}

fn classify_udpip_opcode(opcode: u8) -> Option<(EtwNetworkOp, u8)> {
    match opcode {
        udpip_opcode::SEND_IPV4 => Some((EtwNetworkOp::UdpSend, 4)),
        udpip_opcode::RECV_IPV4 => Some((EtwNetworkOp::UdpRecv, 4)),
        udpip_opcode::SEND_IPV6 => Some((EtwNetworkOp::UdpSend, 6)),
        udpip_opcode::RECV_IPV6 => Some((EtwNetworkOp::UdpRecv, 6)),
        _ => None,
    }
}

fn parse_udpip_event(opcode: u8, version: u8, data: &[u8]) -> Option<NetworkEtwRecord> {
    let (operation, ip_version) = classify_udpip_opcode(opcode)?;
    let mut cursor = NetCursor::new(data);

    match version {
        1 => {
            if ip_version != 4 {
                return None;
            }
            let pid = cursor.u32_le()?;
            let size = cursor.u32_le()?;
            let daddr = cursor.ip_addr(4)?;
            let saddr = cursor.ip_addr(4)?;
            let dport = cursor.u16_be()?;
            let sport = cursor.u16_be()?;
            Some(NetworkEtwRecord {
                provider: EtwNetworkProvider::UdpIp,
                operation,
                ip_version: 4,
                pid,
                size,
                daddr,
                saddr,
                dport,
                sport,
                seqnum: None,
                conn_id: None,
            })
        }
        2 => {
            let pid = cursor.u32_le()?;
            let size = cursor.u32_le()?;
            let daddr = cursor.ip_addr(ip_version)?;
            let saddr = cursor.ip_addr(ip_version)?;
            let dport = cursor.u16_be()?;
            let sport = cursor.u16_be()?;
            let seqnum = cursor.u32_le()?;
            let conn_id = cursor.u32_le()?;
            Some(NetworkEtwRecord {
                provider: EtwNetworkProvider::UdpIp,
                operation,
                ip_version,
                pid,
                size,
                daddr,
                saddr,
                dport,
                sport,
                seqnum: Some(seqnum),
                conn_id: Some(conn_id),
            })
        }
        _ => None,
    }
}

#[cfg(test)]
pub(super) mod tests {
    use super::*;

    pub(crate) fn build_tcpip_v2_payload(
        pid: u32,
        size: u32,
        daddr: IpAddr,
        saddr: IpAddr,
        dport: u16,
        sport: u16,
        extra_zero_bytes: usize,
        seqnum: u32,
        conn_id: u32,
    ) -> Vec<u8> {
        let mut data = Vec::new();
        data.extend(pid.to_le_bytes());
        data.extend(size.to_le_bytes());
        match (daddr, saddr) {
            (IpAddr::V4(d), IpAddr::V4(s)) => {
                data.extend(d.octets());
                data.extend(s.octets());
            }
            (IpAddr::V6(d), IpAddr::V6(s)) => {
                data.extend(d.octets());
                data.extend(s.octets());
            }
            _ => panic!("mismatched IP versions"),
        }
        data.extend(dport.to_be_bytes());
        data.extend(sport.to_be_bytes());
        data.extend(std::iter::repeat_n(0_u8, extra_zero_bytes));
        data.extend(seqnum.to_le_bytes());
        data.extend(conn_id.to_le_bytes());
        data
    }

    pub(crate) fn build_udpip_v2_payload(
        pid: u32,
        size: u32,
        daddr: IpAddr,
        saddr: IpAddr,
        dport: u16,
        sport: u16,
        seqnum: u32,
        conn_id: u32,
    ) -> Vec<u8> {
        build_tcpip_v2_payload(pid, size, daddr, saddr, dport, sport, 0, seqnum, conn_id)
    }

    #[test]
    fn parses_tcpip_v2_ipv4_connect_accept_and_standard_events() {
        let connect_payload = build_tcpip_v2_payload(
            4242,
            0,
            IpAddr::V4(Ipv4Addr::new(93, 184, 216, 34)),
            IpAddr::V4(Ipv4Addr::new(192, 168, 1, 10)),
            443,
            51234,
            16,
            11,
            0xfeed_beef,
        );
        let rec = parse_network_event(
            EtwNetworkProvider::TcpIp,
            tcpip_opcode::CONNECT_IPV4,
            2,
            &connect_payload,
        )
        .unwrap();
        assert_eq!(rec.operation, EtwNetworkOp::TcpConnect);
        assert_eq!(rec.ip_version, 4);
        assert_eq!(rec.pid, 4242);
        assert_eq!(rec.local_endpoint(), "192.168.1.10:51234");
        assert_eq!(rec.peer_endpoint(), "93.184.216.34:443");
        assert_eq!(rec.primary_port(), 443);
        assert_eq!(rec.seqnum, Some(11));
        assert_eq!(rec.conn_id, Some(0xfeed_beef));

        let accept_rec = parse_network_event(
            EtwNetworkProvider::TcpIp,
            tcpip_opcode::ACCEPT_IPV4,
            2,
            &connect_payload,
        )
        .unwrap();
        assert_eq!(accept_rec.operation, EtwNetworkOp::TcpAccept);
        assert_eq!(accept_rec.primary_port(), 51234);

        let disconnect_payload = build_tcpip_v2_payload(
            4242,
            128,
            IpAddr::V4(Ipv4Addr::new(127, 0, 0, 1)),
            IpAddr::V4(Ipv4Addr::new(127, 0, 0, 1)),
            8080,
            55000,
            0,
            22,
            0x1234,
        );
        let disc = parse_network_event(
            EtwNetworkProvider::TcpIp,
            tcpip_opcode::DISCONNECT_IPV4,
            2,
            &disconnect_payload,
        )
        .unwrap();
        assert_eq!(disc.operation, EtwNetworkOp::TcpDisconnect);
        assert_eq!(disc.size, 128);
        assert_eq!(disc.peer_endpoint(), "127.0.0.1:8080");

        let send_payload = build_tcpip_v2_payload(
            4242,
            256,
            IpAddr::V4(Ipv4Addr::new(127, 0, 0, 1)),
            IpAddr::V4(Ipv4Addr::new(127, 0, 0, 1)),
            8080,
            55000,
            8,
            33,
            0x5678,
        );
        let send = parse_network_event(
            EtwNetworkProvider::TcpIp,
            tcpip_opcode::SEND_IPV4,
            2,
            &send_payload,
        )
        .unwrap();
        assert_eq!(send.operation, EtwNetworkOp::TcpSend);
        assert_eq!(send.seqnum, Some(33));
        assert_eq!(send.conn_id, Some(0x5678));
    }

    #[test]
    fn parses_tcpip_v2_ipv6_layouts_with_bracketed_endpoints() {
        let daddr = IpAddr::V6("2001:4860:4860::8888".parse().unwrap());
        let saddr = IpAddr::V6("::1".parse().unwrap());
        let accept_payload =
            build_tcpip_v2_payload(777, 0, daddr, saddr, 443, 8443, 16, 1, 0xaaaa_bbbb);
        let accept = parse_network_event(
            EtwNetworkProvider::TcpIp,
            tcpip_opcode::ACCEPT_IPV6,
            2,
            &accept_payload,
        )
        .unwrap();
        assert_eq!(accept.ip_version, 6);
        assert_eq!(accept.local_endpoint(), "[::1]:8443");
        assert_eq!(accept.peer_endpoint(), "[2001:4860:4860::8888]:443");
        assert_eq!(accept.primary_port(), 8443);

        let send_payload = build_tcpip_v2_payload(777, 64, daddr, saddr, 443, 8443, 8, 2, 0xcccc);
        let send = parse_network_event(
            EtwNetworkProvider::TcpIp,
            tcpip_opcode::SEND_IPV6,
            2,
            &send_payload,
        )
        .unwrap();
        assert_eq!(send.operation, EtwNetworkOp::TcpSend);
        assert_eq!(send.operation.operation_name(6), "SendIPV6");

        let reconn_payload = build_tcpip_v2_payload(777, 0, daddr, saddr, 443, 8443, 0, 3, 0xdddd);
        let reconn = parse_network_event(
            EtwNetworkProvider::TcpIp,
            tcpip_opcode::RECONNECT_IPV6,
            2,
            &reconn_payload,
        )
        .unwrap();
        assert_eq!(reconn.operation, EtwNetworkOp::TcpReconnect);
        assert_eq!(reconn.operation.event_name(), "NET_RECONNECT");
    }

    #[test]
    fn parses_tcpip_v1_swapped_connid_seqnum_and_v0_layout() {
        let mut v1 = Vec::new();
        v1.extend(55_u32.to_le_bytes());
        v1.extend(512_u32.to_le_bytes());
        v1.extend([10, 0, 0, 2]);
        v1.extend([10, 0, 0, 1]);
        v1.extend(9000_u16.to_be_bytes());
        v1.extend(50000_u16.to_be_bytes());
        v1.extend(0x1111_2222_u32.to_le_bytes()); // connid first in v1
        v1.extend(99_u32.to_le_bytes()); // seqnum second in v1
        let rec_v1 =
            parse_network_event(EtwNetworkProvider::TcpIp, tcpip_opcode::RECV_IPV4, 1, &v1)
                .unwrap();
        assert_eq!(rec_v1.conn_id, Some(0x1111_2222));
        assert_eq!(rec_v1.seqnum, Some(99));
        assert_eq!(rec_v1.dport, 9000);
        assert_eq!(rec_v1.sport, 50000);

        let mut v0 = Vec::new();
        v0.extend([1, 1, 1, 1]);
        v0.extend([192, 168, 0, 5]);
        v0.extend(443_u16.to_be_bytes());
        v0.extend(60001_u16.to_be_bytes());
        v0.extend(100_u32.to_le_bytes());
        v0.extend(888_u32.to_le_bytes());
        let rec_v0 = parse_network_event(
            EtwNetworkProvider::TcpIp,
            tcpip_opcode::CONNECT_IPV4,
            0,
            &v0,
        )
        .unwrap();
        assert_eq!(rec_v0.pid, 888);
        assert_eq!(rec_v0.size, 100);
        assert_eq!(rec_v0.peer_endpoint(), "1.1.1.1:443");
        assert_eq!(rec_v0.local_endpoint(), "192.168.0.5:60001");
        assert_eq!(rec_v0.seqnum, None);
        assert_eq!(rec_v0.conn_id, None);
    }

    #[test]
    fn parses_udpip_v1_and_v2_ipv4_and_ipv6() {
        let mut v1 = Vec::new();
        v1.extend(99_u32.to_le_bytes());
        v1.extend(48_u32.to_le_bytes());
        v1.extend([8, 8, 8, 8]);
        v1.extend([192, 168, 1, 20]);
        v1.extend(53_u16.to_be_bytes());
        v1.extend(53535_u16.to_be_bytes());
        let rec_v1 =
            parse_network_event(EtwNetworkProvider::UdpIp, udpip_opcode::SEND_IPV4, 1, &v1)
                .unwrap();
        assert_eq!(rec_v1.operation, EtwNetworkOp::UdpSend);
        assert_eq!(rec_v1.operation.event_name(), "NET_UDP_SEND");
        assert_eq!(rec_v1.peer_endpoint(), "8.8.8.8:53");
        assert_eq!(rec_v1.seqnum, None);

        let v2_v6 = build_udpip_v2_payload(
            1234,
            72,
            IpAddr::V6("2606:4700:4700::1111".parse().unwrap()),
            IpAddr::V6("::1".parse().unwrap()),
            443,
            54321,
            7,
            0x42,
        );
        let rec_v2 = parse_network_event(
            EtwNetworkProvider::UdpIp,
            udpip_opcode::RECV_IPV6,
            2,
            &v2_v6,
        )
        .unwrap();
        assert_eq!(rec_v2.operation, EtwNetworkOp::UdpRecv);
        assert_eq!(rec_v2.ip_version, 6);
        assert_eq!(rec_v2.peer_endpoint(), "[2606:4700:4700::1111]:443");
        assert_eq!(rec_v2.conn_id, Some(0x42));
    }

    #[test]
    fn rejects_truncated_and_unsupported_network_payloads() {
        let connect_v4 = build_tcpip_v2_payload(
            1,
            0,
            IpAddr::V4(Ipv4Addr::LOCALHOST),
            IpAddr::V4(Ipv4Addr::LOCALHOST),
            443,
            50000,
            16,
            1,
            2,
        );
        assert!(
            parse_network_event(
                EtwNetworkProvider::TcpIp,
                tcpip_opcode::CONNECT_IPV4,
                2,
                &connect_v4[..connect_v4.len() - 1],
            )
            .is_none()
        );
        assert!(
            parse_network_event(
                EtwNetworkProvider::TcpIp,
                tcpip_opcode::CONNECT_IPV4,
                3,
                &connect_v4,
            )
            .is_none()
        );
        assert!(
            parse_network_event(
                EtwNetworkProvider::TcpIp,
                tcpip_opcode::CONNECT_IPV6,
                1,
                &connect_v4,
            )
            .is_none()
        );
        assert!(
            parse_network_event(
                EtwNetworkProvider::TcpIp,
                tcpip_opcode::FAIL,
                2,
                &connect_v4,
            )
            .is_none()
        );

        let udp_v2 = build_udpip_v2_payload(
            1,
            10,
            IpAddr::V4(Ipv4Addr::LOCALHOST),
            IpAddr::V4(Ipv4Addr::LOCALHOST),
            53,
            40000,
            1,
            2,
        );
        assert!(
            parse_network_event(
                EtwNetworkProvider::UdpIp,
                udpip_opcode::SEND_IPV4,
                2,
                &udp_v2[..udp_v2.len() - 1],
            )
            .is_none()
        );
        assert!(
            parse_network_event(
                EtwNetworkProvider::UdpIp,
                udpip_opcode::SEND_IPV4,
                0,
                &udp_v2,
            )
            .is_none()
        );
        assert!(
            parse_network_event(EtwNetworkProvider::UdpIp, udpip_opcode::FAIL, 2, &udp_v2)
                .is_none()
        );
    }

    #[test]
    fn callback_allowlist_filters_per_packet_and_fail_opcodes() {
        for opcode in [
            tcpip_opcode::CONNECT_IPV4,
            tcpip_opcode::DISCONNECT_IPV4,
            tcpip_opcode::ACCEPT_IPV4,
            tcpip_opcode::RECONNECT_IPV4,
            tcpip_opcode::CONNECT_IPV6,
            tcpip_opcode::DISCONNECT_IPV6,
            tcpip_opcode::ACCEPT_IPV6,
            tcpip_opcode::RECONNECT_IPV6,
        ] {
            assert!(
                should_capture_in_callback(EtwNetworkProvider::TcpIp, opcode),
                "expected tcpip opcode {opcode} allowed"
            );
        }
        for opcode in [
            tcpip_opcode::SEND_IPV4,
            tcpip_opcode::RECV_IPV4,
            tcpip_opcode::RETRANSMIT_IPV4,
            tcpip_opcode::FAIL,
            tcpip_opcode::TCP_COPY_IPV4,
            tcpip_opcode::SEND_IPV6,
            tcpip_opcode::RECV_IPV6,
            tcpip_opcode::RETRANSMIT_IPV6,
            tcpip_opcode::TCP_COPY_IPV6,
        ] {
            assert!(
                !should_capture_in_callback(EtwNetworkProvider::TcpIp, opcode),
                "expected tcpip opcode {opcode} filtered"
            );
        }

        assert!(should_capture_in_callback(
            EtwNetworkProvider::UdpIp,
            udpip_opcode::SEND_IPV4
        ));
        assert!(should_capture_in_callback(
            EtwNetworkProvider::UdpIp,
            udpip_opcode::SEND_IPV6
        ));
        assert!(!should_capture_in_callback(
            EtwNetworkProvider::UdpIp,
            udpip_opcode::RECV_IPV4
        ));
        assert!(!should_capture_in_callback(
            EtwNetworkProvider::UdpIp,
            udpip_opcode::RECV_IPV6
        ));
        assert!(!should_capture_in_callback(
            EtwNetworkProvider::UdpIp,
            udpip_opcode::FAIL
        ));
    }
}

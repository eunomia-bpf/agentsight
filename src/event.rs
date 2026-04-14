use crate::probes::proctrace::VariableEvent as ProcEvent;
use crate::probes::sslsniff::SslEvent;
use crate::probes::procmon::Event as ProcMonEvent;

/// Unified event type that can represent any probe event
///
/// Both variants are lightweight and can be stored directly.
#[derive(Debug)]
pub enum Event {
    Ssl(SslEvent),
    Proc(ProcEvent),
    ProcMon(ProcMonEvent),
}

impl Event {
    /// Get the message type name for logging/debugging
    pub fn event_type(&self) -> &'static str {
        match self {
            Event::Ssl(_) => "Ssl",
            Event::Proc(_) => "Proc",
            Event::ProcMon(_) => "ProcMon",
        }
    }
}

impl Event {
    /// Check if this is an SSL event
    pub fn is_ssl(&self) -> bool {
        matches!(self, Event::Ssl(_))
    }

    /// Check if this is a process event
    pub fn is_proc(&self) -> bool {
        matches!(self, Event::Proc(_))
    }

    /// Check if this is a procmon event
    pub fn is_procmon(&self) -> bool {
        matches!(self, Event::ProcMon(_))
    }

    /// Get SSL event if this is one
    pub fn as_ssl(&self) -> Option<&SslEvent> {
        match self {
            Event::Ssl(e) => Some(e),
            _ => None,
        }
    }

    /// Get process event if this is one
    pub fn as_proc(&self) -> Option<&ProcEvent> {
        match self {
            Event::Proc(e) => Some(e),
            _ => None,
        }
    }

    /// Get procmon event if this is one
    pub fn as_procmon(&self) -> Option<&ProcMonEvent> {
        match self {
            Event::ProcMon(e) => Some(e),
            _ => None,
        }
    }
}

# SSL payload byte fidelity

`sslsniff` emits both `data` and `data_hex` for every nonempty captured SSL
read or write. `data` is readable JSON text. `data_hex` is the exact captured
plaintext byte sequence encoded as lowercase hexadecimal and is the input for
binary protocol parsers, including HTTP/2 HPACK. A JSON reader can decode a
valid UTF-8 sequence in `data` into one character, so converting that string
back to bytes can corrupt a binary header block.

`data_hex` contains only the bytes copied by the probe. Check `buf_size`,
`len`, and `truncated` before treating it as a complete SSL operation. The
field contains plaintext and should receive the same handling as `data`.

If an HPACK header block is malformed, the HTTP/2 parser drops that block and
resets its decoder state. Later independently decodable headers can still be
captured; headers that depend on the lost dynamic table may remain unavailable
until the peer sends a fresh representation.

## Oversized and truncated HTTP/1.1 messages

The HTTP/1.1 parser keeps at most 1 MiB per message, and a single SSL record is
captured up to 256 KiB (`truncated: true` marks a record that lost its tail).
A message that hits either limit is not dropped: the parser emits the HTTP
event for what it saw — start line, parsed headers and the body prefix — and
marks it so a consumer can tell that a larger message existed:

- `body_truncated: true` is present only on such events; complete messages do
  not carry it.
- `body_truncation_reason` is `body_limit` (the 1 MiB cap was reached) or
  `capture_truncated` (an SSL record lost its tail).
- `body_captured_bytes` is the number of body bytes actually retained.
- `content_length` is the size the peer declared, when it sent one, so
  `body_captured_bytes < content_length` shows how much was cut. Chunked and
  close-delimited messages have no declared size.

`body` (and `body_hex`) is a prefix and must not be parsed as a complete
document or decompressed. Bytes of the same message that arrive after the cut
are ignored; the parser resynchronizes on the next message start.

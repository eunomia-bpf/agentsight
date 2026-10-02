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

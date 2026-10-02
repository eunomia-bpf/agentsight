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

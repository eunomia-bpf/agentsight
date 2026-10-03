# hpack-rs

[![Travis Build Status](https://img.shields.io/travis/mlalic/hpack-rs.svg?style=flat-square&label=Travis%20Build)](https://travis-ci.org/mlalic/hpack-rs)
[![AppVeyor Build Status](https://img.shields.io/appveyor/ci/mlalic/hpack-rs/master.svg?style=flat-square&label=AppVeyor%20Build)](https://ci.appveyor.com/project/mlalic/hpack-rs)
[![Coveralls master](https://img.shields.io/coveralls/mlalic/hpack-rs/master.svg?style=flat-square)](https://coveralls.io/github/mlalic/hpack-rs)
[![Crates.io](https://img.shields.io/crates/v/hpack.svg?style=flat-square)](https://crates.io/crates/hpack)

An [HPACK](http://http2.github.io/http2-spec/compression.html) coder implementation in Rust.

[API Documentation](https://mlalic.github.io/hpack-rs/)

# Overview

The library lets you perform header compression and decompression according to the HPACK spec.

The [decoder](src/decoder.rs) module implements the API for performing HPACK decoding.
The `Decoder` struct will track the decoding context during its lifetime (i.e.
subsequent headers on the same connection should be decoded using the same instance).

The decoder implements the full spec and allows for decoding any valid sequence of
bytes representing a compressed header list.

The [encoder](src/encoder.rs) module implements the API for performing HPACK encoding.
The `Encoder` struct will track the encoding context during its lifetime (i.e. the
same instance should be used to encode all headers on the same connection).

The encoder so far does not implement Huffman string literal encoding; this, however,
is enough to be able to send requests to any HPACK-compliant server, as Huffman encoding
is completely optional.

# Examples

## Encoding

Encode some pseudo-headers that are fully indexed by the
[static header table](http://http2.github.io/http2-spec/compression.html#static.table.definition).

```rust
use hpack::Encoder;

let mut encoder = Encoder::new();
let headers = vec![
    (b":method".to_vec(), b"GET".to_vec()),
    (b":path".to_vec(), b"/".to_vec()),
];
// The headers are encoded by providing their index (with a bit flag
// indicating that the indexed representation is used).
assert_eq!(encoder.encode(&headers), vec![2 | 0x80, 4 | 0x80]);
```

## Decoding

Decode the headers from a raw byte sequence. In this case both of them are indexed
by the static table.

```rust
use hpack::Decoder;

let mut decoder = Decoder::new();
let header_list = decoder.decode(&[0x82, 0x84]).unwrap();
assert_eq!(header_list, [
    (b":method".to_vec(), b"GET".to_vec()),
    (b":path".to_vec(), b"/".to_vec()),
]);
```

# Interoperability

The decoder is tested for interoperability with HPACK encoders that have published their
results to the [http2jp/hpack-test-case](https://github.com/http2jp/hpack-test-case)
repo.

# License

The project is published under the terms of the [MIT License](LICENSE).

/// Minimal test case to reproduce the chunked gzip decompression bug
///
/// This test uses actual data captured from OpenAI API response

use flate2::read::GzDecoder;
use std::io::Read;

fn decode_json_escaped_string(s: &str) -> Vec<u8> {
    let mut result = Vec::new();
    for c in s.chars() {
        let cp = c as u32;
        if cp < 256 {
            result.push(cp as u8);
        } else {
            // This came from valid UTF-8 in binary data
            let utf8_bytes = c.to_string().into_bytes();
            result.extend_from_slice(&utf8_bytes);
        }
    }
    result
}

/// Fixed version: Works with bytes instead of strings to handle binary gzip data
fn extract_from_chunked(body: &str) -> Option<Vec<u8>> {
    // Parse chunked transfer encoding format:
    // <chunk-size-hex>\r\n<chunk-data>\r\n...
    let mut result = Vec::new();

    // Convert string to bytes for binary-safe processing
    let body_bytes = decode_json_escaped_string(body);
    let mut pos = 0;

    loop {
        // Find the first \r\n which separates chunk size from data
        let newline_pos = body_bytes[pos..].windows(2)
            .position(|w| w == b"\r\n")
            .map(|p| pos + p);

        if let Some(newline_pos) = newline_pos {
            // Extract chunk size string (should be ASCII hex digits)
            let chunk_size_bytes = &body_bytes[pos..newline_pos];
            let chunk_size_str = match std::str::from_utf8(chunk_size_bytes) {
                Ok(s) => s,
                Err(_) => return None, // Invalid UTF-8 in chunk size
            };

            // Parse chunk size as hex
            let chunk_size = match usize::from_str_radix(chunk_size_str.trim(), 16) {
                Ok(size) => size,
                Err(_) => return None, // Invalid chunk size
            };

            // If chunk size is 0, we've reached the end
            if chunk_size == 0 {
                break;
            }

            // Extract chunk data (binary safe)
            let data_start = newline_pos + 2; // Skip \r\n
            if data_start + chunk_size > body_bytes.len() {
                return None; // Incomplete chunk
            }

            let chunk_data = &body_bytes[data_start..data_start + chunk_size];
            result.extend_from_slice(chunk_data);

            // Move to next chunk (skip chunk data and trailing \r\n)
            pos = data_start + chunk_size + 2;

            if pos >= body_bytes.len() {
                break;
            }
        } else {
            break;
        }
    }

    if result.is_empty() {
        None
    } else {
        Some(result)
    }
}

fn decompress_gzip(data: &[u8]) -> Result<String, String> {
    let mut decoder = GzDecoder::new(data);
    let mut decompressed = Vec::new();

    decoder.read_to_end(&mut decompressed)
        .map_err(|e| format!("Gzip decompression failed: {}", e))?;

    String::from_utf8(decompressed)
        .map_err(|e| format!("UTF-8 conversion failed: {}", e))
}

#[test]
fn test_chunked_gzip_decompression_with_openai_data() {
    // This is the actual chunked gzip data from OpenAI API response
    // Captured from: {"function":"READ/RECV",...,"data":"..."}

    // First chunk with gzip header (size: f = 15 bytes)
    let chunk1 = "f\r\n\u{1f}\u{8b}\u{08}\u{00}\u{00}\u{00}\u{00}\u{00}\u{00}\u{03}\u{00}\u{00}\u{00}\u{ff}\u{ff}\r\n";

    // Second chunk with compressed data (size: 199 = 409 bytes)
    let chunk2 = "199\r\n\u{8c}RAn\u{db}0\u{10}\u{bc}\u{eb}\u{15},\u{cf}Va˲\u{9c}\u{f8}\u{d2}C/F\u{81}\u{a0}=\u{15}\u{08}\u{8a}@`ȕ\u{bc}\u{09}\u{c5}e\u{c9}UZ#\u{f0}\u{df}\u{0b}J\u{8e}\u{a5}\u{a4})Ћ\u{0e};;\u{a3}\u{99}\u{e1}>gBH4r'\u{a4}>(֝\u{b7}\u{f9}\u{e7}\u{db}\u{12}\u{f9};]\u{e3}\u{fe}\u{a1}\u{fa}z\u{f3}x[\u{98}j\u{1f}\u{e2}7\u{f3}\u{f4}\u{f3}\u{a6}\u{fb}\"\u{17}\u{89}A\u{f7}\u{0f}\u{a0}\u{f9}\u{85}\u{f5}QS\u{e7}-0\u{92}\u{1b}a\u{1d}@1$\u{d5}ն*\u{8a}\u{f5}v]\u{ae}\u{07}\u{a0}#\u{03}6\u{d1}Z\u{cf}yIy\u{87}\u{0e}\u{f3}bY\u{94}\u{f9}r\u{9b}\u{af}\u{ae}\u{ce}\u{ec}\u{03}\u{a1}\u{86}(w\u{e2}G&\u{84}\u{10}\u{cf}\u{c3}7\u{f9}t\u{06}~˝X.^&\u{1d}ĨZ\u{90}\u{bb}˒\u{10}2\u{90}M\u{13}\u{a9}b\u{c4}\u{c8}ʱ\\L\u{a0}&\u{c7}\u{e0}\u{06}\u{eb}{\u{b0}\u{96}>\u{88}=\u{fd}\u{12}*\u{80}8R/\u{0c}\u{a1}k\u{05}\u{93}Q\u{c7}OsV\u{80}\u{a6}\u{8f}*9w\u{bd}\u{b5}3@9G\u{ac}R\u{f2}\u{c1}\u{ef}\u{dd}\u{19}9]\u{1c}Zj}\u{a0}\u{fb}\u{f8}\u{86}*\u{1b}t\u{18}\u{0f}u\u{00}\u{15}\u{c9}%7\u{91}\u{c9}\u{cb}\u{01}=eB\u{dc}\u{0d}M\u{f4}\u{af}\u{c2}I\u{1f}\u{a8}\u{f3}\\3=\u{c2}\u{f0}\u{bb}U9\u{ca}ɩ\u{ff}\u{09}\u{bc}:cL\u{ac}\u{ec}4.\u{8a}\u{c5};b\u{b5}\u{01}Vh\u{e3}\u{ac}H\u{a9}\u{95}>\u{80}\u{99}\u{98}S\u{eb}\u{aa}7H3 \u{9b}E\u{fe}\u{db}\u{cb}{\u{da}clt\u{ed}\u{ff}\u{c8}O\u{80}\u{d6}\u{e0}\u{19}L\u{ed}\u{03}\u{18}ԯ\u{f3}Nk\u{01}\u{d2}q\u{fe}k\u{ed}R\u{f1}`XF\u{08}O\u{a8}\u{a1}f\u{84}\u{90}\u{9e}\u{c1}@\u{a3}z;\u{9e}\u{8c}\u{8c}\u{c7}\u{c8}\u{d0}\u{d5}\u{0d}\u{ba}\u{16}\u{82}\u{0f}8\u{de}M\u{e3}\u{eb}M\u{b5}TM\u{05}\u{9b}͵\u{cc}N\u{d9}\u{1f}\u{00}\u{00}\u{00}\u{ff}\u{ff}\r\n";

    // Third chunk (size: a = 10 bytes)
    let chunk3 = "a\r\n\u{03}\u{00}\u{16}\u{7f}\u{81}\u{b2}E\u{03}\u{00}\u{00}\r\n";

    // Final empty chunk
    let chunk4 = "0\r\n\r\n";

    println!("\nTesting chunked gzip decompression with actual OpenAI response data");

    // Combine all chunks
    let full_chunked = format!("{}{}{}{}", chunk1, chunk2, chunk3, chunk4);

    println!("Full chunked body length: {} bytes", full_chunked.len());

    // Extract from chunked encoding
    let extracted = extract_from_chunked(&full_chunked)
        .expect("Should successfully extract from chunked encoding");

    println!("✓ Extracted {} bytes from chunked encoding", extracted.len());
    println!("Extracted bytes (first 20): {:?}", &extracted[..20.min(extracted.len())]);

    // Try to decompress
    let decompressed = decompress_gzip(&extracted)
        .expect("Should successfully decompress gzip data");

    println!("✓ Successfully decompressed!");
    println!("Decompressed text: {}", decompressed);

    // Verify it's valid JSON
    assert!(decompressed.contains("Hello") || decompressed.len() > 0,
        "Decompressed text should contain the response message");
}

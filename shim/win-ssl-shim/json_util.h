// SPDX-License-Identifier: (LGPL-2.1 OR BSD-2-Clause)
//
// Minimal JSON string escaping that reproduces bpf/jsonl.h's
// json_print_escaped_quoted(): control chars and non-ASCII bytes become \u00XX,
// so the emitted line is valid JSON and parses identically to the Linux
// sslsniff output. Header-only so both the DLL and injector can use it.
#pragma once
#include <string>
#include <cstdio>

namespace as_json {

// Append `len` raw bytes of `buf` to `out` as a quoted, escaped JSON string.
inline void append_escaped_quoted(std::string& out, const char* buf, size_t len) {
    static const char hex[] = "0123456789abcdef";
    out.push_back('"');
    for (size_t i = 0; i < len; ++i) {
        unsigned char c = static_cast<unsigned char>(buf[i]);
        switch (c) {
            case '"':  out += "\\\""; break;
            case '\\': out += "\\\\"; break;
            case '\b': out += "\\b";  break;
            case '\f': out += "\\f";  break;
            case '\n': out += "\\n";  break;
            case '\r': out += "\\r";  break;
            case '\t': out += "\\t";  break;
            default:
                if (c < 0x20 || c >= 0x7f) {
                    out += "\\u00";
                    out.push_back(hex[(c >> 4) & 0xf]);
                    out.push_back(hex[c & 0xf]);
                } else {
                    out.push_back(static_cast<char>(c));
                }
        }
    }
    out.push_back('"');
}

} // namespace as_json

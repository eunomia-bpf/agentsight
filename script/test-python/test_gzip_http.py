#!/usr/bin/env python3
"""
Simple test to generate gzip-compressed HTTP traffic.
"""
import gzip
import http.server
import socketserver
import threading
import time
import urllib.request
import json

class GzipHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        # Read request body
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length > 0 else b''

        # Create response
        response_data = {
            "message": "Hello from test server!",
            "data": "This is compressed gzip data " * 20,  # Make it big enough to compress
            "status": "success"
        }
        response_json = json.dumps(response_data).encode('utf-8')

        # Compress response
        compressed = gzip.compress(response_json)

        # Send response
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Encoding', 'gzip')
        self.send_header('Content-Length', len(compressed))
        self.end_headers()
        self.wfile.write(compressed)

    def log_message(self, format, *args):
        # Suppress log messages
        pass

def run_server():
    PORT = 8899
    with socketserver.TCPServer(("", PORT), GzipHandler) as httpd:
        print(f"Test server running on port {PORT}")
        httpd.handle_request()  # Handle just one request

# Start server in background
server_thread = threading.Thread(target=run_server, daemon=True)
server_thread.start()
time.sleep(0.5)  # Give server time to start

# Make request
print("Making request to test server...")
req = urllib.request.Request(
    'http://localhost:8899/test',
    data=json.dumps({"test": "data"}).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)

try:
    with urllib.request.urlopen(req) as response:
        # Python automatically decompresses gzip
        data = response.read()
        print(f"Received response ({len(data)} bytes)")
        result = json.loads(data)
        print(f"Response: {result['message']}")
        print("\nTest completed successfully!")
except Exception as e:
    print(f"Error: {e}")

time.sleep(0.5)  # Wait a bit for server to complete

#!/usr/bin/env python
from http.server import HTTPServer, SimpleHTTPRequestHandler

class HeaderDumper(SimpleHTTPRequestHandler):
    def do_GET(self):
        try:
            return super().do_GET()
        finally:
            print(self.headers)

server = HTTPServer(("", 8123), HeaderDumper)
server.serve_forever()

import http.server
import socketserver
import socket
import ssl
import threading
import urllib.parse
import requests

PORT_HTTP = 8080
PORT_HTTPS = 8443

class ProxyHTTPRequestHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.handle_request("GET")

    def do_POST(self):
        self.handle_request("POST")

    def do_CONNECT(self):
        # Basic HTTPS tunneling without inspection
        try:
            host, port = self.path.split(":")
            port = int(port)
            with socket.create_connection((host, port)) as remote_socket:
                self.send_response(200, "Connection Established")
                self.end_headers()

                self.connection.setblocking(False)
                remote_socket.setblocking(False)

                while True:
                    try:
                        data = self.connection.recv(8192)
                        if not data:
                            break
                        remote_socket.sendall(data)
                    except:
                        pass

                    try:
                        data = remote_socket.recv(8192)
                        if not data:
                            break
                        self.connection.sendall(data)
                    except:
                        pass
        except Exception as e:
            self.send_error(500, str(e))

    def handle_request(self, method):
        url = urllib.parse.urlsplit(self.path)
        target_url = self.path if url.scheme else f"http://{self.headers['Host']}{self.path}"

        print(f"\n=== {method} {target_url} ===")
        print("Headers:")
        for header, value in self.headers.items():
            print(f"{header}: {value}")

        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length else None

        try:
            response = requests.request(
                method,
                target_url,
                headers={key: val for key, val in self.headers.items() if key.lower() != 'host'},
                data=body,
                allow_redirects=False,
                timeout=10
            )

            self.send_response(response.status_code)
            for key, val in response.headers.items():
                if key.lower() == 'transfer-encoding' and val.lower() == 'chunked':
                    continue  # Avoid issues
                self.send_header(key, val)
            self.end_headers()
            self.wfile.write(response.content)
        except Exception as e:
            self.send_error(502, f"Proxy Error: {str(e)}")

def run_http():
    with socketserver.ThreadingTCPServer(("", PORT_HTTP), ProxyHTTPRequestHandler) as httpd:
        print(f"[*] HTTP proxy listening on port {PORT_HTTP}")
        httpd.serve_forever()

def run_https():
    with socketserver.ThreadingTCPServer(("", PORT_HTTPS), ProxyHTTPRequestHandler) as httpd:
        httpd.socket = ssl.wrap_socket(httpd.socket,
                                       keyfile="key.pem",
                                       certfile="cert.pem",
                                       server_side=True)
        print(f"[*] HTTPS proxy listening on port {PORT_HTTPS}")
        httpd.serve_forever()

if __name__ == "__main__":
    threading.Thread(target=run_http, daemon=True).start()

    try:
        run_https()
    except FileNotFoundError:
        print("[!] SSL cert or key not found. Generate 'cert.pem' and 'key.pem' for HTTPS support.")
        print("Continuing with HTTP only...")
        threading.Event().wait()  # Keep main thread alive

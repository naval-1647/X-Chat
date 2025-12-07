"""
Simple HTTP Server for serving Xchat frontend locally
"""
import http.server
import socketserver
import os
import webbrowser
from threading import Timer

class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="web", **kwargs)
    
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        super().end_headers()
    
    def do_GET(self):
        # Handle routing
        if self.path in ['/login', '/register']:
            self.path = '/auth.html'
        elif self.path == '/':
            self.path = '/auth.html'
        elif self.path in ['/chat', '/dashboard']:
            self.path = '/index.html'
        
        return super().do_GET()

def open_browser():
    webbrowser.open('http://localhost:3001')

if __name__ == "__main__":
    PORT = 3001
    
    # Change to the directory containing this script
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    with socketserver.TCPServer(("", PORT), CustomHandler) as httpd:
        print(f"🌐 Frontend server running at http://localhost:{PORT}")
        print(f"📂 Serving files from: {os.path.join(os.getcwd(), 'web')}")
        print(f"🚀 API Backend running at: http://localhost:8000")
        print(f"\n💡 Open http://localhost:{PORT} in your browser")
        print("Press Ctrl+C to stop the server")
        
        # Open browser after 1 second
        Timer(1.0, open_browser).start()
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 Server stopped!")
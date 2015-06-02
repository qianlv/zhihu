#encoding=utf-8
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from SocketServer import ThreadingMixIn
import threading

class GetHandler(BaseHTTPRequestHandler):
    def do_GET(self, *args, **kwargs):
        message = "Hello World!\n" + threading.currentThread().getName()  
        self.send_response(200)
        self.end_headers()
        self.wfile.write(message)
        return
    def do_POST(self, *args, **kwargs):
        import cgi
        form = cgi.FieldStorage(  
                   fp=self.rfile,
                   headers=self.headers,
                   environ={
                       'REQUEST_METHOD':'POST',
                       'CONTENT_TYPE':self.headers['Content-Type'],
                        }
                   )
        for filed in form.keys():
            print filed, form[filed]
        return

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""

if __name__ == '__main__':
    server = ThreadedHTTPServer(('localhost', 8080), GetHandler)
    print 'Start Server, use <Ctrl-C> to stop'
    server.serve_forever()


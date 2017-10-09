#!/usr/bin/python
import SimpleHTTPServer
import SocketServer

PORT = 8000

if __name__ == "__main__":
    # setup
    Handler = SimpleHTTPServer.SimpleHTTPRequestHandler
    httpd = SocketServer.TCPServer(("", PORT), Handler)

    try:                                    # serve
        print "Serving at port", PORT
        httpd.serve_forever()

    except KeyboardInterrupt:               # die
       print "\nClosing socket..."
       httpd.socket.close()

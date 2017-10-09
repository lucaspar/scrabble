#!/usr/bin/python
import socket
import thread

# constants
HOST = ''               # server address
PORT = 5000             # port
MAX_CONN = 5            # maximum simultaneous connections

def connected(con, client):
    print 'Connected to', client

    while True:
        msg = con.recv(1024)
        if not msg: break
        print client, msg

    print 'Finished connection with', client
    con.close()
    thread.exit()

if __name__ == "__main__":
    tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    orig = (HOST, PORT)

    tcp.bind(orig)
    tcp.listen(MAX_CONN)

    while True:
        con, client = tcp.accept()
        thread.start_new_thread(connected, tuple([con, client]))

    tcp.close()

#!/usr/bin/python
import socket

# constants
HOST = '127.0.0.1'      # server address
PORT = 5000             # port

if __name__ == "__main__":

    # set up socket
    tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    dest = (HOST, PORT)
    tcp.connect(dest)

    # send data
    print 'Use CTRL+X to exit\n'
    msg = raw_input()
    while msg != '\x18':
        tcp.send (msg)
        msg = raw_input()

    # close connection
    tcp.close()

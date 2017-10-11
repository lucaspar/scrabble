#!/usr/bin/python
from Tkinter import *
import threading
import common
import select
import socket
import time
import game
import sys
import ui
import os

# constants
#HOST = '192.168.83.134'     # proxy address
HOST = ''                   # proxy address
PORT = 5000                 # port
FPS = 20                    # frames per second

# game properties
board = []
points = 0
error = ''

################################################################################
class UpdateUI(threading.Thread):

    def __init__(self, name, playing):
        threading.Thread.__init__(self)
        self.name = name
        self.playing = playing

    def run(self):

        # shared game properties
        global board
        global points
        global error

        # set user interface
        gui = ui.Interface()
        gui.setInterface()

        # connect to host
        tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        dest = (HOST, PORT)
        tcp.connect(dest)
        tcp.settimeout(5.0)

        # playing
        try:
            while playing.is_set():
                try:
                    # receive current board
                    res = (tcp.recv(1024)).split(';')
                    board = res[0].split(',')

                    tcp.send('r')                           # ready signal
                    if len(board) > 0:
                        gui.update(board, points, error)    # update UI

                    time.sleep(1/FPS)                  # timeout for redraw

                except socket.timeout:
                    continue

            tcp.close()
            print '\n\t', ':: Update UI loop finished ::'
            print '\n\t', ':: Update UI connection closed ::'

        except:
            e = sys.exc_info()[0]
            playing.clear()
            tcp.close()
            print '\n\t', ':: Update UI interrupted ::', e

################################################################################
class UserInput(threading.Thread):

    def __init__(self, name, playing):
        threading.Thread.__init__(self)
        self.name = name
        self.playing = playing

    def run(self):

        # game properties
        global board
        global points
        global error

        # user input connection
        tcp = common.tcp_client(HOST, PORT+1, timeout=5)

        # play game
        try:
            while playing.is_set():

                # if there's input ready, read it
                while sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                    msg = sys.stdin.readline().strip('\n').lower()
                    if msg:
                        print 'msg:', msg
                        tcp.send(msg)

                        # get result
                        answer = (tcp.recv(1024)).split(';')
                        print 'ans:', answer
                        points = points + float(answer[0])
                        error = answer[1]

                    else: continue       # empty line
                else:
                    time.sleep(0.05)     # no input, sleep before checking again
                    continue

            tcp.close()
            print '\n\t', ':: User input loop finished ::'
            print '\n\t', ':: User input connection closed ::'

        except:
            e = sys.exc_info()[0]
            tcp.close()
            playing.clear()
            print '\n\t', ':: User input interrupted ::', e

################################################################################
if __name__ == "__main__":

    playing = threading.Event()
    playing.set()

    t_update_ui = UpdateUI("UPDATE UI", playing)
    t_user_input = UserInput("USER INPUT", playing)

    t_user_input.daemon = True
    t_update_ui.daemon = True

    t_update_ui.start()
    t_user_input.start()

    try:
        while 1:
            time.sleep(1)
    except KeyboardInterrupt:
        print "Attempting to close player threads."
        playing.clear()
        t_update_ui.join(timeout=0.5)
        t_user_input.join(timeout=0.5)

        if t_update_ui.isAlive() or t_user_input.isAlive():
            print 'Bye'
            common.terminate()

        print "Player threads successfully closed :)"
